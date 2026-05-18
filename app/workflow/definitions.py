"""工作流定义模块。

定义 Temporal 工作流类 DevWorkflow，基于统一的 GraphRunner 进行 DAG 遍历和调度。
"""

import asyncio
from datetime import timedelta
from typing import Any, Dict, List, cast

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.workflow.activities import ACTIVITY_MAP
    from app.workflow.dag_runner import DAG, DAGNode
    from app.workflow.graph_runner import ExecutionContext, GraphRunner, StageExecutor


class TemporalStageExecutor(StageExecutor):
    """Temporal 专用的 StageExecutor 实现。

    在 Temporal Workflow 中调用 Activity 来执行阶段。
    """

    def __init__(self, snapshot_result: Dict[str, Any]):
        self.snapshot_result = snapshot_result
        self._results: Dict[str, Any] = {}

    async def on_workflow_start(self, ctx: ExecutionContext):
        """Temporal 中无需额外初始化。"""
        pass

    async def on_workflow_complete(self, ctx: ExecutionContext, status: str):
        """Temporal 中由 DevWorkflow 统一处理完成逻辑。"""
        pass

    async def on_batch_start(self, batch: List[str], ctx: ExecutionContext):
        """批次开始前的回调。"""
        pass

    async def on_batch_complete(self, batch: List[str], ctx: ExecutionContext):
        """批次完成后的回调。"""
        pass

    async def execute(self, node: DAGNode, ctx: ExecutionContext) -> Dict[str, Any]:
        """通过 Temporal Activity 执行单个阶段。"""
        project_id = ctx.project_id
        timeout = node.timeout_seconds or 300

        # 1. 执行 Agent 任务
        execute_result = await workflow.execute_activity(
            cast(Any, ACTIVITY_MAP["execute_agent_task"]),
            args=(
                project_id,
                node.id,
                node.name,
                node.agent_role,
                node.agent,
                node.context,
            ),
            start_to_close_timeout=timedelta(seconds=timeout),
        )

        if execute_result.get("status") == "failed":
            return execute_result

        # 2. 审批节点处理
        if node.requires_approval:
            task_id = execute_result.get("task_id", 0)

            await workflow.execute_activity(
                cast(Any, ACTIVITY_MAP["send_approval_request"]),
                args=(project_id, node.id, node.name, node.agent_role),
                start_to_close_timeout=timedelta(seconds=30),
            )

            approval_result = await workflow.execute_activity(
                cast(Any, ACTIVITY_MAP["wait_for_approval"]),
                args=(project_id, task_id),
                start_to_close_timeout=timedelta(days=7),
            )

            if approval_result.get("status") == "rejected":
                snapshot_id = self.snapshot_result.get("snapshot_id")
                if snapshot_id:
                    await workflow.execute_activity(
                        cast(Any, ACTIVITY_MAP["rollback_state"]),
                        args=(project_id, snapshot_id),
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                return {
                    "status": "rejected",
                    "stage": node.id,
                    "proposal": execute_result,
                }

        return execute_result


@workflow.defn
class DevWorkflow:
    """DevMatrix 开发工作流。

    通过 Temporal 编排多 Agent 协作流程，
    基于统一的 GraphRunner 进行 DAG 拓扑排序执行、并行分支、审批节点和回滚。
    """

    @workflow.run
    async def run(self, config: dict) -> dict:
        project_id = config.get("project_id", "")
        flow_json = config.get("flow_json", "")
        stages = config.get("stages", [])

        if not project_id:
            return {"status": "error", "message": "project_id required"}

        # 优先使用 flow_json（DAG 结构），否则回退到 stages 列表（线性）
        if flow_json:
            try:
                dag = DAG.from_flow_json(flow_json)
            except ValueError as exc:
                return {"status": "error", "message": f"Invalid flow_json: {exc}"}
        elif stages:
            dag = DAG.from_stages(stages)
        else:
            return {"status": "error", "message": "flow_json or stages required"}

        # 创建状态快照
        snapshot_result: Dict[str, Any] = await workflow.execute_activity(
            cast(Any, ACTIVITY_MAP["create_state_snapshot"]),
            args=(project_id,),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # 使用统一的 GraphRunner 进行 DAG 遍历
        runner = GraphRunner(dag)
        executor = TemporalStageExecutor(snapshot_result)
        ctx = ExecutionContext(
            project_id=project_id, metadata=config.get("context", {})
        )

        for batch in runner.iter_batches():
            # batch 中的节点依赖都已满足，可以并行执行
            batch_results = await self._execute_batch(batch, runner, executor, ctx)

            # 检查是否有失败
            if any(
                r.get("status") in ("failed", "rejected")
                for r in batch_results.values()
            ):
                return {
                    "status": "failed",
                    "project_id": project_id,
                    "results": ctx.results,
                }

        # 通知完成
        await workflow.execute_activity(
            cast(Any, ACTIVITY_MAP["notify_completion"]),
            args=(project_id,),
            start_to_close_timeout=timedelta(seconds=30),
        )

        return {
            "status": "completed",
            "project_id": project_id,
            "results": ctx.results,
        }

    async def _execute_batch(
        self,
        batch: List[str],
        runner: GraphRunner,
        executor: TemporalStageExecutor,
        ctx: ExecutionContext,
    ) -> Dict[str, Any]:
        """执行一个批次的节点（并行）。"""
        if len(batch) == 1:
            node_id = batch[0]
            node = runner.get_node(node_id)
            if not node:
                return {node_id: {"status": "failed", "error": "Node not found"}}
            result = await executor.execute(node, ctx)
            if result.get("status") in ("failed", "rejected"):
                runner.failed.add(node_id)
            else:
                runner.completed.add(node_id)
            ctx.set_result(node_id, result)
            return {node_id: result}

        # 多节点并行执行（Temporal 中通过 asyncio.gather 实现并行 Activity）
        async def run_node(node_id: str) -> tuple:
            node = runner.get_node(node_id)
            if not node:
                return node_id, {"status": "failed", "error": "Node not found"}
            result = await executor.execute(node, ctx)
            return node_id, result

        promises = [run_node(nid) for nid in batch]
        results_list = await asyncio.gather(*promises, return_exceptions=True)

        batch_results: Dict[str, Any] = {}
        for item in results_list:
            if isinstance(item, BaseException):
                # BaseException 不可迭代，跳过处理
                continue
            node_id, result = item
            if isinstance(result, Exception):
                batch_results[node_id] = {"status": "failed", "error": str(result)}
                runner.failed.add(node_id)
            else:
                batch_results[node_id] = result
                if result.get("status") in ("failed", "rejected"):
                    runner.failed.add(node_id)
                else:
                    runner.completed.add(node_id)
            ctx.set_result(node_id, batch_results[node_id])

        return batch_results
