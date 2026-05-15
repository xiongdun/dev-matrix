"""需求管理 API 模块。

提供项目需求的创建和列表查询接口。

主要端点：
    - POST /requirements/: 创建新需求
    - GET /requirements/: 分页列出所有需求

使用示例：
    ```python
    from app.api.requirements import router
    app.include_router(router, prefix="/requirements")
    ```
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.state.models import get_db, ProjectStateModel
from app.state.schemas import ProjectState, ProjectStateCreate
from app.state.repository import StateRepository

logger = logging.getLogger(__name__)
router = APIRouter()


class ErrorResponse(BaseModel):
    """错误响应模型。

    Attributes:
        detail: 错误详情。
    """
    detail: str


class PaginatedRequirementsResponse(BaseModel):
    """分页需求列表响应模型。

    Attributes:
        total: 总记录数。
        limit: 每页限制。
        offset: 跳过记录数。
        items: 需求列表。
    """
    total: int
    limit: int
    offset: int
    items: List[ProjectState]


@router.post("/", response_model=ProjectState, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def create_requirement(
    req: ProjectStateCreate,
    db: Session = Depends(get_db),
):
    """创建新项目需求。

    如果项目 ID 已存在则返回 400 错误。

    Args:
        req: 项目创建请求体。
        db: 数据库会话，由依赖注入提供。

    Returns:
        ProjectState: 创建的项目状态。

    Raises:
        HTTPException: 项目已存在返回 400，其他错误返回 500。
    """
    try:
        repo = StateRepository(db)
        existing = repo.get_state(req.project_id)
        if existing:
            logger.warning("Create requirement failed: project '%s' already exists", req.project_id)
            raise HTTPException(status_code=400, detail="Project already exists")
        state = repo.update_state(
            project_id=req.project_id,
            state_json=req.state_json or "{}",
            status=req.status or "pending",
        )
        logger.info("Created requirement for project '%s'", req.project_id)
        return state
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to create requirement for project '%s'", req.project_id)
        raise HTTPException(status_code=500, detail=f"Failed to create requirement: {exc}") from exc


@router.get(
    "/",
    response_model=PaginatedRequirementsResponse,
    responses={500: {"model": ErrorResponse}},
)
async def list_requirements(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
):
    """分页列出所有项目需求。

    按更新时间倒序排列。

    Args:
        db: 数据库会话，由依赖注入提供。
        limit: 每页最大返回数量，默认 100，范围 1-1000。
        offset: 跳过的记录数，默认 0。

    Returns:
        PaginatedRequirementsResponse: 分页需求列表。

    Raises:
        HTTPException: 查询失败时返回 500 错误。
    """
    try:
        total = db.query(ProjectStateModel).count()
        states = (
            db.query(ProjectStateModel)
            .order_by(ProjectStateModel.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        logger.info("Listed %d/%d requirements (limit=%d, offset=%d)", len(states), total, limit, offset)
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": states,
        }
    except Exception as exc:
        logger.exception("Failed to list requirements")
        raise HTTPException(status_code=500, detail=f"Failed to list requirements: {exc}") from exc
