"""审批管理 API 模块。

提供项目审批提交、状态查询、快照列表和回滚功能。

主要端点：
    - POST /approvals/{project_id}: 提交审批
    - GET /approvals/{project_id}/state: 获取项目状态
    - GET /approvals/{project_id}/snapshots: 列出快照
    - POST /approvals/{project_id}/rollback: 回滚到指定快照

使用示例：
    ```python
    from app.api.approvals import router
    app.include_router(router, prefix="/approvals")
    ```
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.state.models import get_db
from app.state.schemas import ProjectState, StateSnapshot
from app.state.repository import StateRepository

logger = logging.getLogger(__name__)
router = APIRouter()


class ErrorResponse(BaseModel):
    """错误响应模型。

    Attributes:
        detail: 错误详情。
    """
    detail: str


@router.post(
    "/{project_id}",
    response_model=ProjectState,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def submit_approval(
    project_id: str,
    status: str = Query(..., pattern="^(approved|rejected)$"),
    comment: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """提交项目审批。

    在更新状态前创建快照，支持审批通过或拒绝。

    Args:
        project_id: 项目 ID。
        status: 审批状态，必须为 "approved" 或 "rejected"。
        comment: 审批备注，可选。
        db: 数据库会话，由依赖注入提供。

    Returns:
        ProjectState: 更新后的项目状态。

    Raises:
        HTTPException: 项目不存在返回 404，其他错误返回 500。
    """
    try:
        repo = StateRepository(db)
        state = repo.get_state(project_id)
        if state is None:
            logger.warning("Approval submission failed: project '%s' not found", project_id)
            raise HTTPException(status_code=404, detail="Project not found")
        repo.create_snapshot(project_id)
        updated = repo.update_state(
            project_id=project_id,
            state_json=state.state_json,
            status=f"approval_{status}",
        )
        logger.info("Submitted approval '%s' for project '%s'", status, project_id)
        if comment:
            logger.debug("Approval comment for project '%s': %s", project_id, comment)
        return updated
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to submit approval for project '%s'", project_id)
        raise HTTPException(status_code=500, detail=f"Failed to submit approval: {exc}") from exc


@router.get(
    "/{project_id}/state",
    response_model=ProjectState,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_project_state(
    project_id: str,
    db: Session = Depends(get_db),
):
    """获取指定项目的当前状态。

    Args:
        project_id: 项目 ID。
        db: 数据库会话，由依赖注入提供。

    Returns:
        ProjectState: 项目状态。

    Raises:
        HTTPException: 项目不存在返回 404，其他错误返回 500。
    """
    try:
        repo = StateRepository(db)
        state = repo.get_state(project_id)
        if state is None:
            logger.warning("Get project state failed: project '%s' not found", project_id)
            raise HTTPException(status_code=404, detail="Project not found")
        logger.debug("Retrieved state for project '%s'", project_id)
        return state
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get project state for '%s'", project_id)
        raise HTTPException(status_code=500, detail=f"Failed to get project state: {exc}") from exc


@router.get(
    "/{project_id}/snapshots",
    response_model=List[StateSnapshot],
    responses={500: {"model": ErrorResponse}},
)
async def list_snapshots(
    project_id: str,
    db: Session = Depends(get_db),
):
    """列出指定项目的所有状态快照。

    按创建时间倒序排列。

    Args:
        project_id: 项目 ID。
        db: 数据库会话，由依赖注入提供。

    Returns:
        List[StateSnapshot]: 快照列表。

    Raises:
        HTTPException: 查询失败时返回 500 错误。
    """
    try:
        repo = StateRepository(db)
        snapshots = repo.get_snapshots(project_id)
        logger.info("Listed %d snapshots for project '%s'", len(snapshots), project_id)
        return snapshots
    except Exception as exc:
        logger.exception("Failed to list snapshots for project '%s'", project_id)
        raise HTTPException(status_code=500, detail=f"Failed to list snapshots: {exc}") from exc


@router.post(
    "/{project_id}/rollback",
    response_model=ProjectState,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def rollback_to_snapshot(
    project_id: str,
    snapshot_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """将项目状态回滚到指定快照。

    Args:
        project_id: 项目 ID。
        snapshot_id: 快照 ID。
        db: 数据库会话，由依赖注入提供。

    Returns:
        ProjectState: 回滚后的项目状态。

    Raises:
        HTTPException: 快照不存在返回 404，其他错误返回 500。
    """
    try:
        repo = StateRepository(db)
        state = repo.rollback_to_snapshot(project_id, snapshot_id)
        logger.info("Rolled back project '%s' to snapshot %d", project_id, snapshot_id)
        return state
    except ValueError as exc:
        logger.warning("Rollback failed for project '%s' to snapshot %d: %s", project_id, snapshot_id, exc)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to rollback project '%s' to snapshot %d", project_id, snapshot_id)
        raise HTTPException(status_code=500, detail=f"Failed to rollback: {exc}") from exc
