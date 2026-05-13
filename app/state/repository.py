import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.state.models import ProjectStateModel, StateSnapshotModel
from app.state.schemas import ProjectStateCreate


class StateRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_state(self, project_id: str) -> Optional[ProjectStateModel]:
        return (
            self.db.query(ProjectStateModel)
            .filter(ProjectStateModel.project_id == project_id)
            .first()
        )

    def update_state(
        self, project_id: str, state_json: str, status: Optional[str] = None
    ) -> ProjectStateModel:
        state = self.get_state(project_id)
        if state is None:
            state = ProjectStateModel(project_id=project_id)
            self.db.add(state)
        state.state_json = state_json
        if status is not None:
            state.status = status
        state.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(state)
        return state

    def create_snapshot(self, project_id: str) -> StateSnapshotModel:
        state = self.get_state(project_id)
        if state is None:
            raise ValueError(f"Project {project_id} not found")
        snapshot = StateSnapshotModel(
            project_id=project_id,
            state_json=state.state_json,
            status=state.status,
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def get_snapshots(self, project_id: str) -> List[StateSnapshotModel]:
        return (
            self.db.query(StateSnapshotModel)
            .filter(StateSnapshotModel.project_id == project_id)
            .order_by(StateSnapshotModel.created_at.desc())
            .all()
        )

    def rollback_to_snapshot(self, project_id: str, snapshot_id: int) -> ProjectStateModel:
        snapshot = (
            self.db.query(StateSnapshotModel)
            .filter(
                StateSnapshotModel.id == snapshot_id,
                StateSnapshotModel.project_id == project_id,
            )
            .first()
        )
        if snapshot is None:
            raise ValueError(f"Snapshot {snapshot_id} not found for project {project_id}")
        return self.update_state(
            project_id=project_id,
            state_json=snapshot.state_json,
            status=snapshot.status,
        )
