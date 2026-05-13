from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.state.models import get_db, ProjectStateModel
from app.state.schemas import ProjectState, ProjectStateCreate
from app.state.repository import StateRepository

router = APIRouter()


@router.post("/", response_model=ProjectState)
async def create_requirement(
    req: ProjectStateCreate,
    db: Session = Depends(get_db),
):
    repo = StateRepository(db)
    existing = repo.get_state(req.project_id)
    if existing:
        raise HTTPException(status_code=400, detail="Project already exists")
    state = repo.update_state(
        project_id=req.project_id,
        state_json=req.state_json or "{}",
        status=req.status or "pending",
    )
    return state


@router.get("/", response_model=List[ProjectState])
async def list_requirements(
    db: Session = Depends(get_db),
):
    states = db.query(ProjectStateModel).all()
    return states
