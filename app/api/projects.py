"""项目管理 API 模块。

提供项目的增删改查 RESTful API。

主要路由：
    - GET    /projects          列表（支持分页、筛选、排序）
    - POST   /projects          创建
    - GET    /projects/{id}     详情
    - PUT    /projects/{id}     更新
    - DELETE /projects/{id}     删除
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.state.models import ProjectModel, get_db

router = APIRouter()


class ProjectCreate(BaseModel):
    """创建项目请求模型。"""

    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)
    owner: str = Field(default="", max_length=64)
    priority: str = Field(default="medium")
    status: str = Field(default="planning")
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    """更新项目请求模型。"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    description: Optional[str] = Field(default=None, max_length=2000)
    owner: Optional[str] = Field(default=None, max_length=64)
    priority: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectOut(BaseModel):
    """项目响应模型。"""

    id: int
    name: str
    description: str
    owner: str
    priority: str
    status: str
    progress: float
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListOut(BaseModel):
    """项目列表响应模型。"""

    items: List[ProjectOut]
    total: int
    page: int
    page_size: int


@router.get("", response_model=ProjectListOut)
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db),
):
    """获取项目列表。

    支持分页、按状态/优先级筛选、关键词搜索、排序。
    """
    query = db.query(ProjectModel)

    if status:
        query = query.filter(ProjectModel.status == status)
    if priority:
        query = query.filter(ProjectModel.priority == priority)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            ProjectModel.name.ilike(like) | ProjectModel.description.ilike(like)
        )

    total = query.count()

    sort_column = getattr(ProjectModel, sort_by, ProjectModel.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return ProjectListOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """创建新项目。"""
    project = ProjectModel(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """获取项目详情。"""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)
):
    """更新项目。"""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目。"""
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None
