"""工作流管线执行器模块。

提供 WorkflowPipeline 类，按配置顺序执行工作流阶段，
支持审批暂停、并行分支、回滚和重试。

主要类：
    - WorkflowPipeline: 工作流管线执行器。
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base import Proposal
from app.events.bus import event_bus
from app.events.types import Event, EventTypes
from app.llm.router import LLMRouter
from app.state.models import get_db, WorkflowTaskModel
from app.state.repository import StateRepository
from app.state.statemachine import StateMachine, ProjectStatus
from app.workflow.pipeline.loader import PipelineLoader
from app.workflow.pipeline.models import PipelineConfig, PipelineStage

logger = logging.getLogger(__name__)


class WorkflowPipeline:
    """工作流管线执行器。

    按配置顺序执行工作流阶段，支持审批暂停、并行分支、回滚和重试。

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
            self.config = PipelineLoader.load(PipelineLoader(), self.config_path.replace("config/", "").replace(".yaml", ""))
            logger.info("Loaded pipeline config from %s", self.config_path)
        except Exception:
            try:
                loader = PipelineLoader()
                self.config = loader.load("workflow-pipeline")
                logger.info("Loaded pipeline config from default")
            except Exception as exc:
                logger.exception("Failed to load pipeline config")
                self.config = None

    async def run(self, project_id: str, initial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.config is None:
            return {"status": "error", "message": "Pipeline config not loaded"}

        db = next(get_db())
        repo = StateRepository(db)
        router = LLMRouter()

        if repo.get_state(project_id) is None:
            repo.update_state(project_id, json.dumps(initial_context or {}, ensure_ascii=False), ProjectStatus.PENDING.value)

        repo.update_state(project_id, repo.get_state(project_id).state_json, ProjectStatus.ANALYZING.value)

        event_bus.publish(Event(type=EventTypes.WORKFLOW_STARTED, payload={"project_id": project_id}, source="pipeline", project_id=project_id))

        snapshot = repo.create_snapshot(project_id)

        stage_map = {s.id: s for s in self.config.stages}
        executed = set()
        results = {}
        context = dict(initial_context or {})

        start_stages = [s for s in self.config.stages if not s.requires]
        if not start_stages:
            start_stages = [self.config.stages[0]] if self.config.stages else []

        try:
            await self._execute_stages(project_id, start_stages, stage_map, executed, results, context, db, repo, router)
            repo.update_state(project_id, repo.get_state(project_id).state_json, ProjectStatus.COMPLETED.value)
            event_bus.publish(Event(type=EventTypes.WORKFLOW_COMPLETED, payload={"project_id": project_id}, source="pipeline", project_id=project_id))
            return {"status": "completed", "project_id": project_id, "results": results}
        except Exception as exc:
            logger.exception("Pipeline failed for project %s", project_id)
            repo.update_state(project_id, repo.get_state(project_id).state_json, ProjectStatus.FAILED.value)
            event_bus.publish(Event(type=EventTypes.WORKFLOW_FAILED, payload={"project_id": project_id, "error": str(exc)}, source="pipeline", project_id=project_id))
            return {"status": "failed", "project_id": project_id, "error": str(exc)}

    async def _execute_stages(
        self, project_id: str, stages: List[PipelineStage], stage_map: Dict[str, PipelineStage],
        executed: set, results: Dict, context: Dict, db, repo: StateRepository, router: LLMRouter
    ):
        parallel_tasks = []
        parallel_stage_ids = []

        for stage in stages:
            if stage.id in executed:
                continue
            parallel_tasks.append(self._execute_single_stage(project_id, stage, stage_map, executed, results, context, db, repo, router))
            parallel_stage_ids.append(stage.id)

        if not parallel_tasks:
            return

        if len(parallel_tasks) == 1:
            await parallel_tasks[0]
        else:
            await asyncio.gather(*parallel_tasks)

    async def _execute_single_stage(
        self, project_id: str, stage: PipelineStage, stage_map: Dict[str, PipelineStage],
        executed: set, results: Dict, context: Dict, db, repo: StateRepository, router: LLMRouter
    ):
        if stage.id in executed:
            return

        executed.add(stage.id)
        logger.info("Executing stage '%s' for project %s", stage.id, project_id)

        status = StateMachine.stage_to_status(stage.id)
        repo.update_state(project_id, repo.get_state(project_id).state_json, status)

        try:
            from app.core.registry.agent_registry import agent_registry

            try:
                agent_cls = agent_registry.get(stage.agent)
            except KeyError:
                raise ValueError(f"Agent '{stage.agent}' not found in registry")

            agent = agent_cls(llm_router=router, state_repository=repo)
            default_timeout = self.config.settings.get("default_timeout", 300) if self.config.settings else 300
            proposal = await asyncio.wait_for(
                agent.run(project_id, context),
                timeout=stage.timeout_seconds or default_timeout,
            )

            current_state = repo.get_state(project_id)
            state_dict = json.loads(current_state.state_json) if current_state and current_state.state_json else {}
            state_dict[stage.id] = {
                "agent": stage.agent,
                "content": proposal.content,
                "metadata": proposal.metadata,
                "timestamp": datetime.utcnow().isoformat(),
            }
            repo.update_state(project_id, json.dumps(state_dict, ensure_ascii=False), status)

            task = WorkflowTaskModel(
                project_id=project_id,
                stage_id=stage.id,
                stage_name=stage.name,
                agent_role=stage.agent,
                status="pending" if stage.requires_approval else "approved",
                output_json=json.dumps({"content": proposal.content, "metadata": proposal.metadata}, ensure_ascii=False),
                arrived_at=datetime.utcnow(),
            )
            if not stage.requires_approval:
                task.processed_at = datetime.utcnow()
            db.add(task)
            db.commit()
            db.refresh(task)

            context[stage.id] = proposal.content
            results[stage.id] = {"status": "completed", "task_id": task.id}

            event_bus.publish(Event(type=EventTypes.AGENT_COMPLETED, payload={"project_id": project_id, "stage_id": stage.id, "agent": stage.agent}, source="pipeline", project_id=project_id))

            if stage.requires_approval:
                repo.update_state(project_id, repo.get_state(project_id).state_json, ProjectStatus.AWAITING_APPROVAL.value)
                event_bus.publish(Event(type=EventTypes.APPROVAL_REQUIRED, payload={"project_id": project_id, "stage_id": stage.id, "task_id": task.id}, source="pipeline", project_id=project_id))

                approval = await self._wait_for_approval(db, task.id, timeout=86400)
                if approval == "approved":
                    repo.update_state(project_id, repo.get_state(project_id).state_json, ProjectStatus.APPROVED.value)
                    event_bus.publish(Event(type=EventTypes.APPROVAL_APPROVED, payload={"project_id": project_id, "stage_id": stage.id}, source="pipeline", project_id=project_id))
                    results[stage.id]["approval"] = "approved"
                elif approval == "rejected":
                    repo.update_state(project_id, repo.get_state(project_id).state_json, ProjectStatus.REJECTED.value)
                    event_bus.publish(Event(type=EventTypes.APPROVAL_REJECTED, payload={"project_id": project_id, "stage_id": stage.id}, source="pipeline", project_id=project_id))
                    results[stage.id]["approval"] = "rejected"

                    retry_approval = await self._wait_for_retry_and_approval(db, task.id, timeout=86400)
                    if retry_approval == "approved":
                        repo.update_state(project_id, repo.get_state(project_id).state_json, ProjectStatus.APPROVED.value)
                        event_bus.publish(Event(type=EventTypes.APPROVAL_APPROVED, payload={"project_id": project_id, "stage_id": stage.id}, source="pipeline", project_id=project_id))
                        results[stage.id]["approval"] = "approved_after_retry"
                    else:
                        return
                else:
                    results[stage.id]["approval"] = "timeout"

            next_stages = stage.get_next_stages()
            if next_stages:
                next_stage_objs = [stage_map[sid] for sid in next_stages if sid in stage_map]
                await self._execute_stages(project_id, next_stage_objs, stage_map, executed, results, context, db, repo, router)

        except asyncio.TimeoutError:
            logger.error("Stage '%s' timed out for project %s", stage.id, project_id)
            results[stage.id] = {"status": "timeout"}
            auto_rollback = self.config.settings.get("auto_rollback_on_failure", False) if self.config.settings else False
            if auto_rollback:
                snapshots = repo.get_snapshots(project_id)
                if snapshots:
                    repo.rollback_to_snapshot(project_id, snapshots[0].id)
            raise
        except Exception as exc:
            logger.exception("Stage '%s' failed for project %s", stage.id, project_id)
            results[stage.id] = {"status": "failed", "error": str(exc)}
            auto_rollback = self.config.settings.get("auto_rollback_on_failure", False) if self.config.settings else False
            if auto_rollback:
                snapshots = repo.get_snapshots(project_id)
                if snapshots:
                    repo.rollback_to_snapshot(project_id, snapshots[0].id)
            raise

    async def _wait_for_approval(self, db, task_id: int, timeout: int = 86400) -> str:
        poll_interval = 3
        elapsed = 0
        while elapsed < timeout:
            task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
            if task:
                if task.status == "approved":
                    return "approved"
                if task.status == "rejected":
                    return "rejected"
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        return "timeout"

    async def _wait_for_retry_and_approval(self, db, task_id: int, timeout: int = 86400) -> str:
        poll_interval = 3
        elapsed = 0
        while elapsed < timeout:
            task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
            if task:
                if task.status == "approved":
                    return "approved"
                if task.status == "rejected":
                    pass
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        return "timeout"
