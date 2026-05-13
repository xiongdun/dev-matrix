from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.state.models import get_db
from app.state.repository import StateRepository
from app.state.schemas import ProjectState

router = APIRouter()


@router.post("/{project_id}/start")
async def start_workflow(
    project_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
):
    repo = StateRepository(db)
    state = repo.get_state(project_id)
    if state is None:
        repo.update_state(
            project_id=project_id,
            state_json="{}",
            status="workflow_started",
        )
    else:
        repo.update_state(
            project_id=project_id,
            state_json=state.state_json,
            status="workflow_started",
        )
    return {"project_id": project_id, "status": "workflow_started"}


@router.get("/{project_id}/status")
async def get_workflow_status(
    project_id: str,
    db: Session = Depends(get_db),
):
    repo = StateRepository(db)
    state = repo.get_state(project_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "project_id": project_id,
        "status": state.status,
        "updated_at": state.updated_at.isoformat() if state.updated_at else None,
    }
