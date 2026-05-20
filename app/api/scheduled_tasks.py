"""定时任务 API 模块。

提供定时任务的增删改查、启用/禁用、立即执行和执行日志查询。

主要端点：
    - GET    /scheduled-tasks          列表
    - POST   /scheduled-tasks          创建
    - GET    /scheduled-tasks/{id}     详情
    - PUT    /scheduled-tasks/{id}     更新
    - DELETE /scheduled-tasks/{id}     删除
    - POST   /scheduled-tasks/{id}/toggle  启用/禁用
    - POST   /scheduled-tasks/{id}/run     立即执行
    - GET    /scheduled-tasks/{id}/logs    执行历史
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.state.models import ScheduledTaskModel, ScheduledTaskLogModel, get_db
from app.scheduler.engine import get_scheduler

logger = logging.getLogger(__name__)
router = APIRouter()


class ScheduledTaskCreate(BaseModel):
    """创建定时任务请求模型。"""

    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    task_type: str = "workflow_instance"
    trigger_type: str = "cron"
    cron_expression: str = ""
    is_enabled: int = 1
    config_json: str = "{}"


class ScheduledTaskUpdate(BaseModel):
    """更新定时任务请求模型。"""

    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    task_type: Optional[str] = None
    trigger_type: Optional[str] = None
    cron_expression: Optional[str] = None
    is_enabled: Optional[int] = None
    config_json: Optional[str] = None


class ScheduledTaskOut(BaseModel):
    """定时任务响应模型。"""

    id: int
    name: str
    description: str
    task_type: str
    trigger_type: str
    cron_expression: str
    is_enabled: int
    config_json: str
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduledTaskLogOut(BaseModel):
    """定时任务日志响应模型。"""

    id: int
    task_id: int
    status: str
    output: str
    error: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def _model_to_out(model: ScheduledTaskModel) -> ScheduledTaskOut:
    return ScheduledTaskOut(
        id=cast(int, model.id),
        name=cast(str, model.name),
        description=cast(str, model.description),
        task_type=cast(str, model.task_type),
        trigger_type=cast(str, model.trigger_type),
        cron_expression=cast(str, model.cron_expression),
        is_enabled=cast(int, model.is_enabled),
        config_json=cast(str, model.config_json),
        last_run_at=cast(Optional[datetime], model.last_run_at),
        next_run_at=cast(Optional[datetime], model.next_run_at),
        created_at=cast(Optional[datetime], model.created_at),
        updated_at=cast(Optional[datetime], model.updated_at),
    )


def _log_to_out(model: ScheduledTaskLogModel) -> ScheduledTaskLogOut:
    return ScheduledTaskLogOut(
        id=cast(int, model.id),
        task_id=cast(int, model.task_id),
        status=cast(str, model.status),
        output=cast(str, model.output),
        error=cast(str, model.error),
        started_at=cast(Optional[datetime], model.started_at),
        completed_at=cast(Optional[datetime], model.completed_at),
    )


@router.get("", response_model=Dict[str, List[ScheduledTaskOut]])
def list_scheduled_tasks(db: Session = Depends(get_db)):
    """获取定时任务列表。"""
    tasks = db.query(ScheduledTaskModel).order_by(ScheduledTaskModel.id.desc()).all()
    return {"tasks": [_model_to_out(t) for t in tasks]}


@router.post("", response_model=ScheduledTaskOut, status_code=201)
def create_scheduled_task(data: ScheduledTaskCreate, db: Session = Depends(get_db)):
    """创建定时任务。"""
    task = ScheduledTaskModel(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)

    scheduler = get_scheduler()
    if scheduler:
        scheduler.add_task(task)

    logger.info("Created scheduled task '%s' (id=%d)", task.name, task.id)
    return _model_to_out(task)


@router.get("/{task_id}", response_model=ScheduledTaskOut)
def get_scheduled_task(task_id: int, db: Session = Depends(get_db)):
    """获取定时任务详情。"""
    task = db.query(ScheduledTaskModel).filter(ScheduledTaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _model_to_out(task)


@router.put("/{task_id}", response_model=ScheduledTaskOut)
def update_scheduled_task(
    task_id: int, data: ScheduledTaskUpdate, db: Session = Depends(get_db)
):
    """更新定时任务。"""
    task = db.query(ScheduledTaskModel).filter(ScheduledTaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    scheduler = get_scheduler()
    if scheduler:
        scheduler.update_task(task)

    logger.info("Updated scheduled task '%s' (id=%d)", task.name, task.id)
    return _model_to_out(task)


@router.delete("/{task_id}", status_code=204)
def delete_scheduled_task(task_id: int, db: Session = Depends(get_db)):
    """删除定时任务。"""
    task = db.query(ScheduledTaskModel).filter(ScheduledTaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    scheduler = get_scheduler()
    if scheduler:
        scheduler.remove_task(task_id)

    db.query(ScheduledTaskLogModel).filter(ScheduledTaskLogModel.task_id == task_id).delete()
    db.delete(task)
    db.commit()

    logger.info("Deleted scheduled task id=%d", task_id)
    return None


@router.post("/{task_id}/toggle", response_model=ScheduledTaskOut)
def toggle_scheduled_task(task_id: int, db: Session = Depends(get_db)):
    """启用/禁用定时任务。"""
    task = db.query(ScheduledTaskModel).filter(ScheduledTaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.is_enabled = 0 if task.is_enabled else 1
    db.commit()
    db.refresh(task)

    scheduler = get_scheduler()
    if scheduler:
        if task.is_enabled:
            scheduler.add_task(task)
        else:
            scheduler.remove_task(task_id)

    logger.info("Toggled scheduled task id=%d to enabled=%d", task_id, task.is_enabled)
    return _model_to_out(task)


@router.post("/{task_id}/run", response_model=ScheduledTaskLogOut)
def run_scheduled_task_now(task_id: int, db: Session = Depends(get_db)):
    """立即执行定时任务。"""
    task = db.query(ScheduledTaskModel).filter(ScheduledTaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not available")

    log = scheduler.execute_task_now(task, db)
    return _log_to_out(log)


@router.get("/{task_id}/logs", response_model=Dict[str, List[ScheduledTaskLogOut]])
def get_scheduled_task_logs(
    task_id: int, limit: int = 50, db: Session = Depends(get_db)
):
    """获取定时任务执行历史。"""
    logs = (
        db.query(ScheduledTaskLogModel)
        .filter(ScheduledTaskLogModel.task_id == task_id)
        .order_by(ScheduledTaskLogModel.id.desc())
        .limit(limit)
        .all()
    )
    return {"logs": [_log_to_out(l) for l in logs]}
