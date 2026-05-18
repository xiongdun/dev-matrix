"""工作流管线执行器模块。

提供 WorkflowPipeline 类，基于统一的 GraphRunner 执行工作流阶段，
支持审批暂停、并行分支、回滚和重试。

主要类：
    - WorkflowPipeline: 工作流管线执行器，使用 GraphRunner 调度。
    - PipelineStageExecutor: Pipeline 专用的 StageExecutor 实现。
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from app.agents.base import Proposal
from app.events.bus import event_bus
from app.events.types import Event, EventTypes
from app.llm.router import LLMRouter
from app.state.models import get_db, WorkflowTaskModel, WorkflowInstanceModel
from app.state.repository import StateRepository
from app.state.statemachine import StateMachine, ProjectStatus
from app.workflow.dag_runner import DAGNode
from app.workflow.graph_runner import ExecutionContext, GraphRunner, StageExecutor
from app.workflow.pipeline.loader import PipelineLoader
from app.workflow.pipeline.models import PipelineConfig

logger = logging.getLogger(__name__)


class PipelineStageExecutor(StageExecutor):
    """Pipeline 专用的阶段执行器。

    实现 StageExecutor 接口，注入数据库、状态仓库和 LLM 路由。
    """

    def __init__(
        self,
        db,
        repo: StateRepository,
        router: LLMRouter,
        config: PipelineConfig,
    ):
        self.db = db
        self.repo = repo
        self.router = router
        self.config = config
        self.instance: Optional[WorkflowInstanceModel] = None

    async def on_workflow_start(self, ctx: ExecutionContext):
        """初始化项目状态和实例记录。"""
        project_id = ctx.project_id

        if self.repo.get_state(project_id) is None:
            self.repo.update_state(
                project_id,
                json.dumps(ctx.metadata, ensure_ascii=False),
                ProjectStatus.PENDING.value,
            )

        current_state = self.repo.get_state(project_id)
        state_json = "{}"
        if current_state is not None and current_state.state_json is not None:
            state_json = str(current_state.state_json)
        self.repo.update_state(
            project_id,
            state_json,
            ProjectStatus.ANALYZING.value,
        )

        self.instance = (
            self.db.query(WorkflowInstanceModel)
            .filter(
                WorkflowInstanceModel.project_id == project_id,
                WorkflowInstanceModel.status.in_(["running", "paused"]),
            )
            .first()
        )

        if self.instance is None:
            from app.api.workflow_config import _generate_instance_id

            instance_id = _generate_instance_id(self.db)
            participants: List[str] = []
            for s in self.config.stages:
                if s.agent and s.agent not in participants:
                    participants.append(s.agent)

            self.instance = WorkflowInstanceModel(
                instance_id=instance_id,
                project_id=project_id,
                current_state="ANALYZING",
                participants=json.dumps(participants, ensure_ascii=False),
                artifacts="[]",
                status="running",
                context_json=json.dumps(ctx.metadata, ensure_ascii=False),
                started_at=datetime.utcnow(),
            )
            self.db.add(self.instance)
            self.db.commit()
            self.db.refresh(self.instance)
        else:
            self.instance.current_state = "ANALYZING"  # type: ignore[assignment]
            self.instance.status = "running"  # type: ignore[assignment]
            self.db.commit()

        await event_bus.publish(
            Event(
                type=EventTypes.WORKFLOW_STARTED,
                payload={
                    "project_id": project_id,
                    "instance_id": self.instance.instance_id,
                },
                source="pipeline",
                project_id=project_id,
            )
        )

        # 创建快照用于回滚
        self.repo.create_snapshot(project_id)

    async def on_workflow_complete(self, ctx: ExecutionContext, status: str):
        """更新项目状态和实例记录。"""
        project_id = ctx.project_id

        if status == "completed":
            current_state = self.repo.get_state(project_id)
            state_json = "{}"
            if current_state is not None and current_state.state_json is not None:
                state_json = str(current_state.state_json)
            self.repo.update_state(
                project_id,
                state_json,
                ProjectStatus.COMPLETED.value,
            )
            if self.instance:
                self.instance.current_state = "COMPLETED"  # type: ignore[assignment]
                self.instance.status = "completed"  # type: ignore[assignment]
                self.instance.completed_at = datetime.utcnow()  # type: ignore[assignment]
                self.db.commit()
            await event_bus.publish(
                Event(
                    type=EventTypes.WORKFLOW_COMPLETED,
                    payload={
                        "project_id": project_id,
                        "instance_id": self.instance.instance_id
                        if self.instance
                        else None,
                    },
                    source="pipeline",
                    project_id=project_id,
                )
            )
        else:
            current_state = self.repo.get_state(project_id)
            state_json = "{}"
            if current_state is not None and current_state.state_json is not None:
                state_json = str(current_state.state_json)
            self.repo.update_state(
                project_id,
                state_json,
                ProjectStatus.FAILED.value,
            )
            if self.instance:
                self.instance.current_state = "FAILED"  # type: ignore[assignment]
                self.instance.status = "failed"  # type: ignore[assignment]
                self.instance.completed_at = datetime.utcnow()  # type: ignore[assignment]
                self.db.commit()
            await event_bus.publish(
                Event(
                    type=EventTypes.WORKFLOW_FAILED,
                    payload={
                        "project_id": project_id,
                        "instance_id": self.instance.instance_id
                        if self.instance
                        else None,
                    },
                    source="pipeline",
                    project_id=project_id,
                )
            )

    async def on_batch_start(self, batch: List[str], ctx: ExecutionContext):
        """批次开始前的回调（Pipeline 无需特殊处理）。"""
        pass

    async def on_batch_complete(self, batch: List[str], ctx: ExecutionContext):
        """批次完成后的回调（Pipeline 无需特殊处理）。"""
        pass

    async def execute(self, node: DAGNode, ctx: ExecutionContext) -> Dict[str, Any]:
        """执行单个阶段。"""
        project_id = ctx.project_id
        stage_id = node.id

        logger.info("Executing stage '%s' for project %s", stage_id, project_id)

        # 更新状态
        status = StateMachine.stage_to_status(stage_id)
        current_state = self.repo.get_state(project_id)
        state_json = "{}"
        if current_state is not None and current_state.state_json is not None:
            state_json = str(current_state.state_json)
        self.repo.update_state(
            project_id,
            state_json,
            status,
        )

        if self.instance:
            self.instance.current_state = stage_id.upper()  # type: ignore[assignment]
            self.db.commit()

        try:
            from app.core.registry.agent_registry import agent_registry

            try:
                agent_cls = agent_registry.get(node.agent)
            except KeyError:
                raise ValueError(f"Agent '{node.agent}' not found in registry")

            agent = agent_cls(llm_router=self.router, state_repository=self.repo)
            default_timeout = (
                self.config.settings.get("default_timeout", 300)
                if self.config.settings
                else 300
            )
            proposal = await asyncio.wait_for(
                agent.run(project_id, ctx.metadata),
                timeout=node.timeout_seconds or default_timeout,
            )

            # 更新状态
            current_state = self.repo.get_state(project_id)
            state_dict: Dict[str, Any] = {}
            if current_state is not None and current_state.state_json is not None:
                state_dict = json.loads(str(current_state.state_json))
            state_dict[stage_id] = {
                "agent": node.agent,
                "content": proposal.content,
                "metadata": proposal.metadata,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.repo.update_state(
                project_id, json.dumps(state_dict, ensure_ascii=False), status
            )

            # 创建任务记录
            task = WorkflowTaskModel(
                project_id=project_id,
                stage_id=stage_id,
                stage_name=node.name,
                agent_role=node.agent,
                status="pending" if node.requires_approval else "approved",
                output_json=json.dumps(
                    {"content": proposal.content, "metadata": proposal.metadata},
                    ensure_ascii=False,
                ),
                arrived_at=datetime.utcnow(),
            )
            if not node.requires_approval:
                task.processed_at = datetime.utcnow()  # type: ignore[assignment]
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            # 更新实例产出物
            if self.instance:
                artifacts: List[Dict[str, Any]] = []
                if self.instance.artifacts is not None:
                    artifacts = json.loads(str(self.instance.artifacts))
                artifacts.append(
                    {
                        "name": f"{stage_id}_output",
                        "stage": stage_id,
                        "agent": node.agent,
                    }
                )
                self.instance.artifacts = json.dumps(artifacts, ensure_ascii=False)  # type: ignore[assignment]
                self.db.commit()

            # 更新上下文
            ctx.metadata[stage_id] = proposal.content
            ctx.add_artifact(f"{stage_id}_output", stage_id, node.agent)

            await event_bus.publish(
                Event(
                    type=EventTypes.AGENT_COMPLETED,
                    payload={
                        "project_id": project_id,
                        "stage_id": stage_id,
                        "agent": node.agent,
                    },
                    source="pipeline",
                    project_id=project_id,
                )
            )

            # 审批处理
            if node.requires_approval:
                task_id_val = cast(int, task.id)
                return await self._handle_approval(
                    project_id, stage_id, task_id_val, proposal
                )

            task_id_val = cast(int, task.id)
            return {"status": "completed", "task_id": task_id_val}

        except asyncio.TimeoutError:
            logger.error("Stage '%s' timed out for project %s", stage_id, project_id)
            self._auto_rollback(project_id)
            return {"status": "timeout", "stage": stage_id}

        except Exception as exc:
            logger.exception("Stage '%s' failed for project %s", stage_id, project_id)
            self._auto_rollback(project_id)
            return {"status": "failed", "error": str(exc), "stage": stage_id}

    async def _handle_approval(
        self, project_id: str, stage_id: str, task_id: int, proposal: Proposal
    ) -> Dict[str, Any]:
        """处理审批节点。"""
        current_state = self.repo.get_state(project_id)
        state_json = "{}"
        if current_state is not None and current_state.state_json is not None:
            state_json = str(current_state.state_json)
        self.repo.update_state(
            project_id,
            state_json,
            ProjectStatus.AWAITING_APPROVAL.value,
        )
        if self.instance:
            self.instance.current_state = f"{stage_id.upper()}_REVIEW"  # type: ignore[assignment]
            self.db.commit()

        await event_bus.publish(
            Event(
                type=EventTypes.APPROVAL_REQUIRED,
                payload={
                    "project_id": project_id,
                    "stage_id": stage_id,
                    "task_id": task_id,
                },
                source="pipeline",
                project_id=project_id,
            )
        )

        approval = await self._wait_for_approval(task_id, timeout=86400)
        if approval == "approved":
            current_state = self.repo.get_state(project_id)
            state_json = "{}"
            if current_state is not None and current_state.state_json is not None:
                state_json = str(current_state.state_json)
            self.repo.update_state(
                project_id,
                state_json,
                ProjectStatus.APPROVED.value,
            )
            await event_bus.publish(
                Event(
                    type=EventTypes.APPROVAL_APPROVED,
                    payload={"project_id": project_id, "stage_id": stage_id},
                    source="pipeline",
                    project_id=project_id,
                )
            )
            return {"status": "completed", "task_id": task_id, "approval": "approved"}

        elif approval == "rejected":
            current_state = self.repo.get_state(project_id)
            state_json = "{}"
            if current_state is not None and current_state.state_json is not None:
                state_json = str(current_state.state_json)
            self.repo.update_state(
                project_id,
                state_json,
                ProjectStatus.REJECTED.value,
            )
            await event_bus.publish(
                Event(
                    type=EventTypes.APPROVAL_REJECTED,
                    payload={"project_id": project_id, "stage_id": stage_id},
                    source="pipeline",
                    project_id=project_id,
                )
            )

            retry_approval = await self._wait_for_retry_and_approval(
                task_id, timeout=86400
            )
            if retry_approval == "approved":
                current_state = self.repo.get_state(project_id)
                state_json = "{}"
                if current_state is not None and current_state.state_json is not None:
                    state_json = str(current_state.state_json)
                self.repo.update_state(
                    project_id,
                    state_json,
                    ProjectStatus.APPROVED.value,
                )
                await event_bus.publish(
                    Event(
                        type=EventTypes.APPROVAL_APPROVED,
                        payload={"project_id": project_id, "stage_id": stage_id},
                        source="pipeline",
                        project_id=project_id,
                    )
                )
                return {
                    "status": "completed",
                    "task_id": task_id,
                    "approval": "approved_after_retry",
                }
            else:
                return {"status": "rejected", "task_id": task_id}

        else:
            return {"status": "completed", "task_id": task_id, "approval": "timeout"}

    def _auto_rollback(self, project_id: str):
        """自动回滚到最近快照。"""
        auto_rollback = (
            self.config.settings.get("auto_rollback_on_failure", False)
            if self.config.settings
            else False
        )
        if auto_rollback:
            snapshots = self.repo.get_snapshots(project_id)
            if snapshots:
                snapshot_id = cast(int, snapshots[0].id)
                self.repo.rollback_to_snapshot(project_id, snapshot_id)

    async def _wait_for_approval(self, task_id: int, timeout: int = 86400) -> str:
        """等待人工审批。"""
        poll_interval = 3
        elapsed = 0
        while elapsed < timeout:
            task = (
                self.db.query(WorkflowTaskModel)
                .filter(WorkflowTaskModel.id == task_id)
                .first()
            )
            if task:
                if task.status == "approved":
                    return "approved"
                if task.status == "rejected":
                    return "rejected"
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        return "timeout"

    async def _wait_for_retry_and_approval(
        self, task_id: int, timeout: int = 86400
    ) -> str:
        """等待重试后的审批。"""
        poll_interval = 3
        elapsed = 0
        while elapsed < timeout:
            task = (
                self.db.query(WorkflowTaskModel)
                .filter(WorkflowTaskModel.id == task_id)
                .first()
            )
            if task:
                if task.status == "approved":
                    return "approved"
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        return "timeout"


class WorkflowPipeline:
    """工作流管线执行器。

    基于统一的 GraphRunner 调度工作流阶段，支持审批暂停、并行分支、回滚和重试。

    Example:
        pipeline = WorkflowPipeline()
        result = await pipeline.run("project_1")
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/workflow-pipeline.yaml"
        self.config: Optional[PipelineConfig] = None
        self._load_config()

    def _load_config(self):
        try:
            self.config = PipelineLoader.load(
                PipelineLoader(),
                self.config_path.replace("config/", "").replace(".yaml", ""),
            )
            logger.info("Loaded pipeline config from %s", self.config_path)
        except Exception:
            try:
                loader = PipelineLoader()
                self.config = loader.load("workflow-pipeline")
                logger.info("Loaded pipeline config from default")
            except Exception:
                logger.exception("Failed to load pipeline config")
                self.config = None

    async def run(
        self,
        project_id: str,
        initial_context: Optional[Dict[str, Any]] = None,
        template_id: Optional[int] = None,
        flow_json: Optional[str] = None,
    ) -> Dict[str, Any]:
        """执行工作流。

        Args:
            project_id: 项目 ID
            initial_context: 初始上下文
            template_id: 模板 ID
            flow_json: Vue Flow 的 JSON 图结构（优先使用）

        Returns:
            执行结果
        """
        if self.config is None:
            return {"status": "error", "message": "Pipeline config not loaded"}

        db = next(get_db())
        repo = StateRepository(db)
        router = LLMRouter()

        # 优先使用 flow_json，否则回退到 stages 配置
        if flow_json:
            runner = GraphRunner.from_flow_json(flow_json)
        else:
            stages = [s.to_dict() for s in self.config.stages]
            runner = GraphRunner.from_stages(stages)

        executor = PipelineStageExecutor(db, repo, router, self.config)
        return await runner.run(project_id, executor, initial_context)
