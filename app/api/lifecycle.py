"""流程实例生命周期管理 API。

提供流程实例的暂停、恢复、取消等操作。
"""

import logging
from typing import Optional, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.state.models import ProjectStateModel, get_db
from app.state.statemachine import ProjectStatus

logger = logging.getLogger(__name__)
router = APIRouter()


class LifecycleAction(BaseModel):
    reason: Optional[str] = None


@router.post("/{project_id}/pause")
async def pause_workflow(project_id: str, db: Session = Depends(get_db)):
    state = (
        db.query(ProjectStateModel)
        .filter(ProjectStateModel.project_id == project_id)
        .first()
    )
    if state is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    status_val = cast(str, state.status)
    if status_val in (ProjectStatus.COMPLETED.value, ProjectStatus.FAILED.value):
        raise HTTPException(
            status_code=400, detail=f"Cannot pause workflow in status '{status_val}'"
        )
    state.status = "paused"  # type: ignore[assignment]
    db.commit()
    logger.info("Paused workflow for project %s", project_id)
    return {"status": "paused", "project_id": project_id}


@router.post("/{project_id}/resume")
async def resume_workflow(project_id: str, db: Session = Depends(get_db)):
    state = (
        db.query(ProjectStateModel)
        .filter(ProjectStateModel.project_id == project_id)
        .first()
    )
    if state is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    status_val = cast(str, state.status)
    if status_val != "paused":
        raise HTTPException(
            status_code=400,
            detail=f"Can only resume from 'paused', current: '{status_val}'",
        )
    state.status = ProjectStatus.ANALYZING.value  # type: ignore[assignment]
    db.commit()
    logger.info("Resumed workflow for project %s", project_id)
    return {"status": "resumed", "project_id": project_id}


@router.post("/{project_id}/cancel")
async def cancel_workflow(
    project_id: str,
    payload: Optional[LifecycleAction] = None,
    db: Session = Depends(get_db),
):
    state = (
        db.query(ProjectStateModel)
        .filter(ProjectStateModel.project_id == project_id)
        .first()
    )
    if state is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    status_val = cast(str, state.status)
    if status_val == ProjectStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Cannot cancel completed workflow")
    reason = payload.reason if payload else None
    state.status = ProjectStatus.FAILED.value  # type: ignore[assignment]
    db.commit()
    logger.info("Cancelled workflow for project %s (reason: %s)", project_id, reason)
    return {"status": "cancelled", "project_id": project_id, "reason": reason}
