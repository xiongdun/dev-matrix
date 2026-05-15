"""工作流活动模块。

定义 Temporal 工作流中执行的活动函数。
每个活动对应工作流中的一个原子操作。

主要活动：
    - create_state_snapshot: 创建状态快照
    - send_approval_request: 发送审批请求
    - execute_agent_task: 执行 Agent 任务
    - wait_for_approval: 等待审批结果
    - rollback_state: 回滚状态
    - notify_completion: 通知完成
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.agents.base import Proposal
from app.events.bus import event_bus
from app.events.types import Event, EventTypes
from app.state.models import get_db, WorkflowTaskModel
from app.state.repository import StateRepository
from app.state.statemachine import StateMachine, ProjectStatus

logger = logging.getLogger(__name__)


def _get_repo() -> StateRepository:
    from app.llm.router import LLMRouter
    db = next(get_db())
    return StateRepository(db)


async def create_state_snapshot(project_id: str, **kwargs) -> Dict[str, Any]:
    repo = _get_repo()
    try:
        snapshot = repo.create_snapshot(project_id)
        logger.info("Created snapshot %d for project %s", snapshot.id, project_id)
        return {"snapshot_id": snapshot.id, "project_id": project_id}
    except Exception as exc:
        logger.exception("Failed to create snapshot for project %s", project_id)
        return {"error": str(exc)}


async def send_approval_request(
    project_id: str, stage_id: str, stage_name: str, agent_role: str, **kwargs
) -> Dict[str, Any]:
    event = Event(
        type=EventTypes.APPROVAL_REQUIRED,
        payload={"project_id": project_id, "stage_id": stage_id, "stage_name": stage_name, "agent_role": agent_role},
        source="workflow",
        project_id=project_id,
    )
    event_bus.publish(event)
    logger.info("Sent approval request for project %s stage %s", project_id, stage_id)
    return {"status": "approval_requested", "project_id": project_id, "stage_id": stage_id}


async def execute_agent_task(
    project_id: str,
    stage_id: str,
    stage_name: str,
    agent_role: str,
    agent_name: str,
    context: Dict[str, Any],
    **kwargs,
) -> Dict[str, Any]:
    from app.core.registry.agent_registry import agent_registry
    from app.llm.router import LLMRouter

    db = next(get_db())
    repo = StateRepository(db)
    router = LLMRouter()

    try:
        try:
            agent_cls = agent_registry.get(agent_name)
        except KeyError:
            raise ValueError(f"Agent '{agent_name}' not found in registry")

        agent = agent_cls(llm_router=router, state_repository=repo)

        status = StateMachine.stage_to_status(stage_id)
        repo.update_state(project_id, repo.get_state(project_id).state_json if repo.get_state(project_id) else "{}", status)

        proposal = await agent.run(project_id, context)

        current_state = repo.get_state(project_id)
        state_dict = json.loads(current_state.state_json) if current_state and current_state.state_json else {}
        state_dict[stage_id] = {
            "agent": agent_name,
            "content": proposal.content,
            "metadata": proposal.metadata,
            "timestamp": datetime.utcnow().isoformat(),
        }
        repo.update_state(project_id, json.dumps(state_dict, ensure_ascii=False), status)

        task = WorkflowTaskModel(
            project_id=project_id,
            stage_id=stage_id,
            stage_name=stage_name,
            agent_role=agent_role,
            status="pending",
            output_json=json.dumps({"content": proposal.content, "metadata": proposal.metadata}, ensure_ascii=False),
            arrived_at=datetime.utcnow(),
        )
        db.add(task)
        db.commit()

        logger.info("Agent %s executed for project %s stage %s", agent_name, project_id, stage_id)
        return {
            "status": "completed",
            "project_id": project_id,
            "stage_id": stage_id,
            "proposal_content": proposal.content,
            "proposal_metadata": proposal.metadata,
            "task_id": task.id,
        }
    except Exception as exc:
        logger.exception("Agent %s failed for project %s stage %s", agent_name, project_id, stage_id)
        repo.update_state(project_id, repo.get_state(project_id).state_json if repo.get_state(project_id) else "{}", ProjectStatus.FAILED.value)
        return {"status": "failed", "error": str(exc), "project_id": project_id, "stage_id": stage_id}


async def wait_for_approval(
    project_id: str, task_id: int, timeout_seconds: int = 86400, **kwargs
) -> Dict[str, Any]:
    db = next(get_db())
    poll_interval = 3
    elapsed = 0

    while elapsed < timeout_seconds:
        task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
        if task is None:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            continue

        if task.status == "approved":
            logger.info("Task %d approved for project %s", task_id, project_id)
            return {"status": "approved", "task_id": task_id}

        if task.status == "rejected":
            logger.info("Task %d rejected for project %s", task_id, project_id)
            return {"status": "rejected", "task_id": task_id, "feedback": task.feedback}

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    logger.warning("Approval timeout for task %d project %s", task_id, project_id)
    return {"status": "timeout", "task_id": task_id}


async def rollback_state(project_id: str, snapshot_id: int, **kwargs) -> Dict[str, Any]:
    repo = _get_repo()
    try:
        repo.rollback_to_snapshot(project_id, snapshot_id)
        event_bus.publish(Event(
            type=EventTypes.ROLLBACK_PERFORMED,
            payload={"project_id": project_id, "snapshot_id": snapshot_id},
            source="workflow",
            project_id=project_id,
        ))
        logger.info("Rolled back project %s to snapshot %d", project_id, snapshot_id)
        return {"status": "rolled_back", "project_id": project_id, "snapshot_id": snapshot_id}
    except Exception as exc:
        logger.exception("Rollback failed for project %s", project_id)
        return {"status": "failed", "error": str(exc)}


async def notify_completion(project_id: str, **kwargs) -> Dict[str, Any]:
    event_bus.publish(Event(
        type=EventTypes.WORKFLOW_COMPLETED,
        payload={"project_id": project_id},
        source="workflow",
        project_id=project_id,
    ))
    repo = _get_repo()
    repo.update_state(project_id, repo.get_state(project_id).state_json if repo.get_state(project_id) else "{}", ProjectStatus.COMPLETED.value)
    logger.info("Workflow completed for project %s", project_id)
    return {"status": "completed", "project_id": project_id}


ACTIVITY_MAP = {
    "create_state_snapshot": create_state_snapshot,
    "send_approval_request": send_approval_request,
    "execute_agent_task": execute_agent_task,
    "wait_for_approval": wait_for_approval,
    "rollback_state": rollback_state,
    "notify_completion": notify_completion,
}
