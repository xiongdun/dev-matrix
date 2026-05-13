from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.state.models import get_db
from app.state.schemas import ProjectState, StateSnapshot
from app.state.repository import StateRepository

router = APIRouter()


@router.post("/{project_id}", response_model=ProjectState)
async def submit_approval(
    project_id: str,
    status: str = Query(..., regex="^(approved|rejected)$"),
    comment: Optional[str] = None,
    db: Session = Depends(get_db),
):
    repo = StateRepository(db)
    state = repo.get_state(project_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Project not found")
    repo.create_snapshot(project_id)
    updated = repo.update_state(
        project_id=project_id,
        state_json=state.state_json,
        status=f"approval_{status}",
    )
    return updated


@router.get("/{project_id}/state", response_model=ProjectState)
async def get_project_state(
    project_id: str,
    db: Session = Depends(get_db),
):
    repo = StateRepository(db)
    state = repo.get_state(project_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return state


@router.get("/{project_id}/snapshots", response_model=List[StateSnapshot])
async def list_snapshots(
    project_id: str,
    db: Session = Depends(get_db),
):
    repo = StateRepository(db)
    snapshots = repo.get_snapshots(project_id)
    return snapshots


@router.post("/{project_id}/rollback", response_model=ProjectState)
async def rollback_to_snapshot(
    project_id: str,
    snapshot_id: int = Query(...),
    db: Session = Depends(get_db),
):
    repo = StateRepository(db)
    try:
        state = repo.rollback_to_snapshot(project_id, snapshot_id)
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
