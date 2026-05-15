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
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.events.bus import event_bus
from app.events.types import Event, EventTypes
from app.state.models import WorkflowTaskModel, get_db

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
        id=model.id,
        project_id=model.project_id,
        workflow_id=model.workflow_id,
        stage_id=model.stage_id,
        stage_name=model.stage_name,
        agent_role=model.agent_role,
        status=model.status,
        output_json=model.output_json,
        feedback=model.feedback,
        arrived_at=model.arrived_at,
        processed_at=model.processed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
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
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {exc}") from exc


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
        raise HTTPException(status_code=400, detail=f"Task {task_id} cannot be approved in status '{task.status}'")
    try:
        task.status = "approved"
        task.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(task)

        event_bus.publish(Event(
            type=EventTypes.APPROVAL_APPROVED,
            payload={"project_id": task.project_id, "stage_id": task.stage_id, "task_id": task.id},
            source="workbench",
            project_id=task.project_id,
        ))
        logger.info("Approved task %d (project=%s, stage=%s)", task.id, task.project_id, task.stage_id)
        return _model_to_response(task)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to approve task %d", task_id)
        raise HTTPException(status_code=500, detail=f"Failed to approve task: {exc}") from exc


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
        raise HTTPException(status_code=400, detail=f"Task {task_id} cannot be rejected in status '{task.status}'")
    try:
        task.status = "rejected"
        task.processed_at = datetime.utcnow()
        if payload and payload.comment:
            task.feedback = payload.comment
        db.commit()
        db.refresh(task)
        logger.info("Rejected task %d (project=%s, stage=%s)", task.id, task.project_id, task.stage_id)
        return _model_to_response(task)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to reject task %d", task_id)
        raise HTTPException(status_code=500, detail=f"Failed to reject task: {exc}") from exc


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
        raise HTTPException(status_code=400, detail=f"Task {task_id} can only be retried from 'rejected' status, current: '{task.status}'")
    try:
        task.status = "retrying"
        task.processed_at = datetime.utcnow()
        if payload and payload.feedback:
            task.feedback = payload.feedback
        db.commit()
        db.refresh(task)

        try:
            from app.core.registry.agent_registry import agent_registry
            from app.llm.router import LLMRouter

            try:
                agent_cls = agent_registry.get(task.agent_role)
            except KeyError:
                agent_cls = None

            if agent_cls:
                router = LLMRouter()
                repo = StateRepository(db)
                agent = agent_cls(llm_router=router, state_repository=repo)
                context = {"feedback": task.feedback, "previous_output": json.loads(task.output_json) if task.output_json else {}}
                proposal = await agent.run(task.project_id, context)

                task.output_json = json.dumps({"content": proposal.content, "metadata": proposal.metadata}, ensure_ascii=False)
                task.status = "pending"
                task.feedback = None
                db.commit()
                db.refresh(task)
                logger.info("Agent re-executed for task %d, new proposal generated", task.id)
        except Exception as agent_exc:
            logger.exception("Agent re-execution failed for task %d: %s", task.id, agent_exc)
            task.status = "rejected"
            db.commit()
            db.refresh(task)

        return _model_to_response(task)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to retry task %d", task_id)
        raise HTTPException(status_code=500, detail=f"Failed to retry task: {exc}") from exc


@router.get("/stats", response_model=TaskStatsResponse)
async def get_stats(
    role: Optional[str] = Query(None, max_length=64),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(WorkflowTaskModel)
        if role:
            query = query.filter(WorkflowTaskModel.agent_role == role)
        tasks = query.all()
        pending = sum(1 for t in tasks if t.status in ("pending", "retrying"))
        completed = sum(1 for t in tasks if t.status == "approved" or t.status == "completed")
        rejected = sum(1 for t in tasks if t.status == "rejected")
        logger.info("Workbench stats (role=%s): pending=%d, completed=%d, rejected=%d", role, pending, completed, rejected)
        return TaskStatsResponse(pending=pending, completed=completed, rejected=rejected)
    except Exception as exc:
        logger.exception("Failed to get workbench stats")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {exc}") from exc
