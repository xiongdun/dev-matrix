"""工作台 API 模块。

提供工作台（Workbench）的任务管理和审批接口，
供前端工作台界面获取待办任务、审批/打回/重试任务以及查看统计。

主要端点：
    - GET /tasks - 获取指定角色的待办任务列表
    - GET /tasks/{task_id} - 获取单个任务详情
    - POST /tasks/{task_id}/approve - 确认通过任务
    - POST /tasks/{task_id}/reject - 打回任务
    - POST /tasks/{task_id}/retry - AI 重新处理任务
    - GET /stats - 获取任务统计

使用示例：
    ```python
    from app.api.workbench import router
    app.include_router(router, prefix="/workbench")
    ```
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.events.bus import event_bus
from app.events.types import Event, EventTypes
from app.state.models import WorkflowTaskModel, get_db
from app.state.repository import StateRepository

logger = logging.getLogger(__name__)
router = APIRouter()


class WorkflowTaskResponse(BaseModel):
    id: int
    project_id: str
    workflow_id: Optional[int] = None
    stage_id: str
    stage_name: str
    agent_role: str
    status: str
    output_json: str = "{}"
    feedback: Optional[str] = None
    arrived_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RejectRequest(BaseModel):
    comment: Optional[str] = Field(None, max_length=2000)


class RetryRequest(BaseModel):
    feedback: Optional[str] = Field(None, max_length=2000)


class TaskStatsResponse(BaseModel):
    pending: int = 0
    completed: int = 0
    rejected: int = 0


def _model_to_response(model: WorkflowTaskModel) -> WorkflowTaskResponse:
    return WorkflowTaskResponse(
        id=cast(int, model.id),
        project_id=cast(str, model.project_id),
        workflow_id=cast(Optional[int], model.workflow_id),
        stage_id=cast(str, model.stage_id),
        stage_name=cast(str, model.stage_name),
        agent_role=cast(str, model.agent_role),
        status=cast(str, model.status),
        output_json=cast(str, model.output_json),
        feedback=cast(Optional[str], model.feedback),
        arrived_at=cast(Optional[datetime], model.arrived_at),
        processed_at=cast(Optional[datetime], model.processed_at),
        created_at=cast(Optional[datetime], model.created_at),
        updated_at=cast(Optional[datetime], model.updated_at),
    )


@router.get("/tasks", response_model=Dict[str, List[WorkflowTaskResponse]])
async def list_tasks(
    role: Optional[str] = Query(None, max_length=64),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(WorkflowTaskModel).filter(
            WorkflowTaskModel.status.in_(["pending", "retrying"])
        )
        if role:
            query = query.filter(WorkflowTaskModel.agent_role == role)
        tasks = query.order_by(WorkflowTaskModel.arrived_at.asc()).all()
        logger.info("Listed %d workbench tasks (role=%s)", len(tasks), role)
        return {"tasks": [_model_to_response(t) for t in tasks]}
    except Exception as exc:
        logger.exception("Failed to list workbench tasks")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/tasks/{task_id}", response_model=WorkflowTaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return _model_to_response(task)


@router.post("/tasks/{task_id}/approve", response_model=WorkflowTaskResponse)
async def approve_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if task.status not in ("pending", "retrying"):
        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} cannot be approved in status '{task.status}'",
        )
    try:
        # type: ignore[assignment]
        task.status = "approved"  # type: ignore[assignment]
        task.processed_at = datetime.utcnow()  # type: ignore[assignment]
        db.commit()
        db.refresh(task)

        await event_bus.publish(
            Event(
                type=EventTypes.APPROVAL_APPROVED,
                payload={
                    "project_id": cast(str, task.project_id),
                    "stage_id": cast(str, task.stage_id),
                    "task_id": cast(int, task.id),
                },
                source="workbench",
                project_id=cast(str, task.project_id),
            )
        )
        logger.info(
            "Approved task %d (project=%s, stage=%s)",
            cast(int, task.id),
            cast(str, task.project_id),
            cast(str, task.stage_id),
        )
        return _model_to_response(task)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to approve task %d", task_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/tasks/{task_id}/reject", response_model=WorkflowTaskResponse)
async def reject_task(
    task_id: int,
    payload: Optional[RejectRequest] = None,
    db: Session = Depends(get_db),
):
    task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if task.status not in ("pending", "retrying"):
        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} cannot be rejected in status '{task.status}'",
        )
    try:
        task.status = "rejected"  # type: ignore[assignment]
        task.processed_at = datetime.utcnow()  # type: ignore[assignment]
        if payload and payload.comment:
            task.feedback = payload.comment  # type: ignore[assignment]
        db.commit()
        db.refresh(task)
        logger.info(
            "Rejected task %d (project=%s, stage=%s)",
            cast(int, task.id),
            cast(str, task.project_id),
            cast(str, task.stage_id),
        )
        return _model_to_response(task)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to reject task %d", task_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/tasks/{task_id}/retry", response_model=WorkflowTaskResponse)
async def retry_task(
    task_id: int,
    payload: Optional[RetryRequest] = None,
    db: Session = Depends(get_db),
):
    task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if task.status != "rejected":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Task {task_id} can only be retried from 'rejected' status, "
                f"current: '{task.status}'"
            ),
        )
    try:
        task.status = "retrying"  # type: ignore[assignment]
        task.processed_at = datetime.utcnow()  # type: ignore[assignment]
        if payload and payload.feedback:
            task.feedback = payload.feedback  # type: ignore[assignment]
        db.commit()
        db.refresh(task)

        try:
            from app.core.registry.agent_registry import agent_registry
            from app.llm.router import LLMRouter

            try:
                agent_cls = agent_registry.get(cast(str, task.agent_role))
            except KeyError:
                agent_cls = None

            if agent_cls:
                router = LLMRouter()
                repo = StateRepository(db)
                agent = agent_cls(llm_router=router, state_repository=repo)
                output_json_val = cast(str, task.output_json)
                context: Dict[str, Any] = {
                    "feedback": task.feedback,
                    "previous_output": json.loads(output_json_val)
                    if output_json_val
                    else {},
                }
                proposal = await agent.run(cast(str, task.project_id), context)

                task.output_json = json.dumps(  # type: ignore[assignment]
                    {"content": proposal.content, "metadata": proposal.metadata},
                    ensure_ascii=False,
                )
                task.status = "pending"  # type: ignore[assignment]
                task.feedback = None  # type: ignore[assignment]
                db.commit()
                db.refresh(task)
                logger.info(
                    "Agent re-executed for task %d, new proposal generated", cast(int, task.id)
                )
        except Exception as agent_exc:
            logger.exception(
                "Agent re-execution failed for task %d: %s", cast(int, task.id), agent_exc
            )
            task.status = "rejected"  # type: ignore[assignment]
            db.commit()
            db.refresh(task)

        return _model_to_response(task)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to retry task %d", task_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/stats", response_model=TaskStatsResponse)
async def get_stats(
    role: Optional[str] = Query(None, max_length=64),
    db: Session = Depends(get_db),
):
    try:
        base_filter = [WorkflowTaskModel.agent_role == role] if role else []
        pending = (
            db.query(func.count(WorkflowTaskModel.id))
            .filter(*base_filter, WorkflowTaskModel.status.in_(["pending", "retrying"]))
            .scalar()
            or 0
        )

        completed = (
            db.query(func.count(WorkflowTaskModel.id))
            .filter(
                *base_filter, WorkflowTaskModel.status.in_(["approved", "completed"])
            )
            .scalar()
            or 0
        )

        rejected = (
            db.query(func.count(WorkflowTaskModel.id))
            .filter(*base_filter, WorkflowTaskModel.status == "rejected")
            .scalar()
            or 0
        )

        logger.info(
            "Workbench stats (role=%s): pending=%d, completed=%d, rejected=%d",
            role,
            pending,
            completed,
            rejected,
        )
        return TaskStatsResponse(
            pending=pending, completed=completed, rejected=rejected
        )
    except Exception as exc:
        logger.exception("Failed to get workbench stats")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
