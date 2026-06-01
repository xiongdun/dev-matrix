"""统一 GraphRunner 抽象层。

提供工作流图遍历和调度的统一接口，被 Temporal Workflow 使用。

核心设计：
    - GraphRunner: 纯图遍历逻辑，不依赖任何执行环境
    - StageExecutor: 抽象接口，由调用方实现具体的阶段执行逻辑
    - ExecutionContext: 共享执行上下文

Example (Temporal):
    runner = GraphRunner.from_flow_json(flow_json)
    for batch in runner.iter_batches():
        # Temporal 中并行执行 batch
        ...
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.workflow.dag_runner import DAG, DAGNode

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """工作流执行上下文，跨阶段共享状态。"""

    project_id: str
    results: dict[str, Any] = field(default_factory=dict)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def set_result(self, stage_id: str, result: Any):
        self.results[stage_id] = result

    def get_result(self, stage_id: str) -> Any:
        return self.results.get(stage_id)

    def add_artifact(self, name: str, stage: str, agent: str, content: Any = None):
        artifact = {"name": name, "stage": stage, "agent": agent}
        if content is not None:
            artifact["content"] = content
        self.artifacts.append(artifact)


class StageExecutor(ABC):
    """阶段执行器抽象接口。

    Temporal 实现此接口，注入执行逻辑。
    """

    @abstractmethod
    async def execute(self, node: DAGNode, ctx: ExecutionContext) -> dict[str, Any]:
        """执行单个阶段。

        Returns:
            执行结果字典，必须包含 "status" 字段：
            - "completed": 成功
            - "failed": 失败
            - "rejected": 审批被拒
        """
        ...

    @abstractmethod
    async def on_batch_start(self, batch: list[str], ctx: ExecutionContext):
        """批次开始前的回调。"""
        ...

    @abstractmethod
    async def on_batch_complete(self, batch: list[str], ctx: ExecutionContext):
        """批次完成后的回调。"""
        ...

    @abstractmethod
    async def on_workflow_start(self, ctx: ExecutionContext):
        """工作流开始前的回调。"""
        ...

    @abstractmethod
    async def on_workflow_complete(self, ctx: ExecutionContext, status: str):
        """工作流完成后的回调。"""
        ...


class GraphRunner:
    """统一图执行引擎。

    负责 DAG 拓扑遍历和批次调度，具体的阶段执行委托给 StageExecutor。
    """

    def __init__(self, dag: DAG):
        self.dag = dag
        self.completed: set[str] = set()
        self.failed: set[str] = set()

    @classmethod
    def from_flow_json(cls, flow_json_str: str) -> "GraphRunner":
        """从 Vue Flow JSON 创建 GraphRunner。"""
        dag = DAG.from_flow_json(flow_json_str)
        return cls(dag)

    @classmethod
    def from_stages(cls, stages: list[dict[str, Any]]) -> "GraphRunner":
        """从阶段列表创建 GraphRunner（线性兼容）。"""
        dag = DAG.from_stages(stages)
        return cls(dag)

    def iter_batches(self):
        """按拓扑层级迭代，每次返回可并行执行的节点 ID 列表。"""
        while len(self.completed) + len(self.failed) < len(self.dag.nodes):
            ready = self.dag.get_ready_nodes(self.completed | self.failed)
            if not ready:
                remaining = set(self.dag.nodes.keys()) - self.completed - self.failed
                if remaining:
                    logger.error("Deadlock detected: nodes %s cannot be scheduled", remaining)
                break
            yield ready

    async def run(
        self,
        project_id: str,
        executor: StageExecutor,
        initial_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """执行完整工作流。

        Args:
            project_id: 项目 ID
            executor: 阶段执行器实现
            initial_context: 初始上下文数据

        Returns:
            工作流执行结果
        """
        ctx = ExecutionContext(
            project_id=project_id,
            metadata=initial_context or {},
        )

        await executor.on_workflow_start(ctx)

        try:
            for batch in self.iter_batches():
                await executor.on_batch_start(batch, ctx)
                batch_results = await self._execute_batch(batch, executor, ctx)
                await executor.on_batch_complete(batch, ctx)

                # 检查是否有失败
                if any(r.get("status") == "failed" for r in batch_results.values()):
                    await executor.on_workflow_complete(ctx, "failed")
                    return {
                        "status": "failed",
                        "project_id": project_id,
                        "results": ctx.results,
                    }

            await executor.on_workflow_complete(ctx, "completed")
            return {
                "status": "completed",
                "project_id": project_id,
                "results": ctx.results,
                "artifacts": ctx.artifacts,
            }

        except Exception as exc:
            logger.exception("Workflow failed for project %s", project_id)
            await executor.on_workflow_complete(ctx, "failed")
            return {
                "status": "failed",
                "project_id": project_id,
                "error": str(exc),
                "results": ctx.results,
            }

    async def _execute_batch(
        self,
        batch: list[str],
        executor: StageExecutor,
        ctx: ExecutionContext,
    ) -> dict[str, Any]:
        """执行一个批次的节点。"""
        import asyncio

        if len(batch) == 1:
            node_id = batch[0]
            node = self.dag.nodes.get(node_id)
            if not node:
                return {node_id: {"status": "failed", "error": "Node not found"}}
            result = await executor.execute(node, ctx)
            if result.get("status") == "failed":
                self.failed.add(node_id)
            else:
                self.completed.add(node_id)
            ctx.set_result(node_id, result)
            return {node_id: result}

        # 并行执行多个节点
        async def run_node(node_id: str) -> tuple[str, dict[str, Any]]:
            node = self.dag.nodes.get(node_id)
            if not node:
                return node_id, {"status": "failed", "error": "Node not found"}
            result = await executor.execute(node, ctx)
            return node_id, result

        tasks = [run_node(nid) for nid in batch]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        batch_results: dict[str, Any] = {}
        for item in results_list:
            if isinstance(item, BaseException):
                continue
            node_id, result = item
            if isinstance(result, Exception):
                batch_results[node_id] = {"status": "failed", "error": str(result)}
                self.failed.add(node_id)
            else:
                batch_results[node_id] = result
                if result.get("status") == "failed":
                    self.failed.add(node_id)
                else:
                    self.completed.add(node_id)
            ctx.set_result(node_id, batch_results[node_id])

        return batch_results

    def get_node(self, node_id: str) -> DAGNode | None:
        """按 ID 获取节点。"""
        return self.dag.nodes.get(node_id)

    def is_done(self) -> bool:
        """检查是否所有节点都已执行完毕。"""
        return len(self.completed) + len(self.failed) >= len(self.dag.nodes)

    def get_ready_nodes(self) -> list[str]:
        """获取当前可执行的节点。"""
        return self.dag.get_ready_nodes(self.completed | self.failed)
