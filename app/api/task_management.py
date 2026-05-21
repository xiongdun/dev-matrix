"""任务管理 API 模块。

提供独立任务系统的增删改查 RESTful API。

主要路由：
    - GET    /tasks          列表（支持筛选、排序）
    - POST   /tasks          创建
    - GET    /tasks/{id}     详情
    - PUT    /tasks/{id}     更新
    - DELETE /tasks/{id}     删除
    - PATCH  /tasks/{id}/status  更新状态（看板拖拽）
    - GET    /tasks/my-tasks  我的任务
"""

import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.state.models import TaskManagementModel, get_db

router = APIRouter()

# Mock 当前用户（后续接入真实用户系统）
MOCK_CURRENT_USER = {"id": "user-001", "name": "当前用户"}


class TaskCreate(BaseModel):
    """创建任务请求模型。"""

    title: str = Field(..., min_length=1, max_length=256)
    description: str = Field(default="", max_length=5000)
    status: str = Field(default="backlog")
    priority: str = Field(default="medium")
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    project_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """更新任务请求模型。"""

    title: Optional[str] = Field(default=None, min_length=1, max_length=256)
    description: Optional[str] = Field(default=None, max_length=5000)
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    project_id: Optional[int] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None


class TaskStatusUpdate(BaseModel):
    """更新任务状态请求模型（看板拖拽用）。"""

    status: str


class TaskOut(BaseModel):
    """任务响应模型。"""

    id: int
    title: str
    description: str
    status: str
    priority: str
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    reporter_id: str
    reporter_name: str
    project_id: Optional[int] = None
    tags: List[str]
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListOut(BaseModel):
    """任务列表响应模型。"""

    items: List[TaskOut]
    total: int


def _model_to_out(task: TaskManagementModel) -> dict:
    """将 ORM 模型转换为字典，处理 tags JSON。"""
    data = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "assignee_id": task.assignee_id,
        "assignee_name": task.assignee_name,
        "reporter_id": task.reporter_id,
        "reporter_name": task.reporter_name,
        "project_id": task.project_id,
        "tags": json.loads(task.tags) if task.tags else [],
        "due_date": task.due_date,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }
    return data


@router.get("", response_model=TaskListOut)
def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[str] = Query(None),
    reporter_id: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db),
):
    """获取任务列表。

    支持按状态、优先级、分配人、创建人、项目筛选，关键词搜索，排序。
    """
    query = db.query(TaskManagementModel)

    if status:
        query = query.filter(TaskManagementModel.status == status)
    if priority:
        query = query.filter(TaskManagementModel.priority == priority)
    if assignee_id:
        query = query.filter(TaskManagementModel.assignee_id == assignee_id)
    if reporter_id:
        query = query.filter(TaskManagementModel.reporter_id == reporter_id)
    if project_id:
        query = query.filter(TaskManagementModel.project_id == project_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            TaskManagementModel.title.ilike(like)
            | TaskManagementModel.description.ilike(like)
        )

    total = query.count()

    sort_column = getattr(TaskManagementModel, sort_by, TaskManagementModel.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    items = query.all()

    return TaskListOut(
        items=[TaskOut(**_model_to_out(item)) for item in items],
        total=total,
    )


@router.post("", response_model=TaskOut, status_code=201)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    """创建新任务。"""
    current_user = MOCK_CURRENT_USER
    task = TaskManagementModel(
        **data.model_dump(exclude={"tags"}),
        reporter_id=current_user["id"],
        reporter_name=current_user["name"],
        tags=json.dumps(data.tags) if data.tags else "[]",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskOut(**_model_to_out(task))


@router.get("/my-tasks", response_model=TaskListOut)
def list_my_tasks(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取当前用户的任务（我创建的 + 分配给我的）。"""
    current_user = MOCK_CURRENT_USER
    query = db.query(TaskManagementModel).filter(
        (TaskManagementModel.reporter_id == current_user["id"])
        | (TaskManagementModel.assignee_id == current_user["id"])
    )

    if status:
        query = query.filter(TaskManagementModel.status == status)

    query = query.order_by(TaskManagementModel.updated_at.desc())
    items = query.all()

    return TaskListOut(
        items=[TaskOut(**_model_to_out(item)) for item in items],
        total=len(items),
    )


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取任务详情。"""
    task = db.query(TaskManagementModel).filter(TaskManagementModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut(**_model_to_out(task))


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    """更新任务。"""
    task = db.query(TaskManagementModel).filter(TaskManagementModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = data.model_dump(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = json.dumps(update_data["tags"])

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return TaskOut(**_model_to_out(task))


@router.patch("/{task_id}/status", response_model=TaskOut)
def update_task_status(
    task_id: int, data: TaskStatusUpdate, db: Session = Depends(get_db)
):
    """更新任务状态（看板拖拽用）。"""
    task = db.query(TaskManagementModel).filter(TaskManagementModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = data.status
    db.commit()
    db.refresh(task)
    return TaskOut(**_model_to_out(task))


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务。"""
    task = db.query(TaskManagementModel).filter(TaskManagementModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return None
