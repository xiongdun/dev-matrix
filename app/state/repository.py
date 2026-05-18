"""状态仓库模块。

提供 StateRepository 类，封装项目状态和快照的数据库操作。

主要类：
    - StateRepository: 状态仓库，管理项目状态和快照的 CRUD。

使用示例：
    ```python
    from app.state.repository import StateRepository
    from app.state.models import get_db

    db = next(get_db())
    repo = StateRepository(db)
    state = repo.get_state("project_1")
    repo.update_state("project_1", '{"key": "value"}', "active")
    ```
"""

from datetime import datetime
from typing import List, Optional, cast

from sqlalchemy.orm import Session

from app.state.models import ProjectStateModel, StateSnapshotModel


class StateRepository:
    """状态仓库，管理项目状态和快照的数据库操作。

    提供状态的查询、更新、快照创建和回滚功能。

    Attributes:
        db: SQLAlchemy 数据库会话。

    Example:
        ```python
        repo = StateRepository(db)
        state = repo.get_state("project_1")
        snapshot = repo.create_snapshot("project_1")
        repo.rollback_to_snapshot("project_1", snapshot.id)
        ```
    """

    def __init__(self, db: Session):
        """初始化状态仓库。

        Args:
            db: SQLAlchemy 数据库会话。
        """
        self.db = db

    def get_state(self, project_id: str) -> Optional[ProjectStateModel]:
        """查询指定项目的当前状态。

        Args:
            project_id: 项目 ID。

        Returns:
            ProjectStateModel: 项目状态，不存在时返回 None。
        """
        return (
            self.db.query(ProjectStateModel)
            .filter(ProjectStateModel.project_id == project_id)
            .first()
        )

    def update_state(
        self,
        project_id: str,
        state_json: str,
        status: Optional[str] = None,
        expected_version: Optional[int] = None,
        skip_transition_check: bool = False,
    ) -> ProjectStateModel:
        state = self.get_state(project_id)
        if state is None:
            state = ProjectStateModel(project_id=project_id)
            self.db.add(state)

        if expected_version is not None and state.version != expected_version:
            raise ValueError(
                f"Optimistic lock conflict: expected version {expected_version}, "
                f"actual {state.version}"
            )

        if status is not None and state.status != status and not skip_transition_check:
            from app.state.statemachine import StateMachine

            current = cast(str, state.status) or "pending"
            try:
                if not StateMachine.can_transition(current, status):
                    raise ValueError(f"Invalid state transition: {current} -> {status}")
            except ValueError:
                if current not in ("pending",) and current != status:
                    pass

        state.state_json = state_json  # type: ignore[assignment]
        if status is not None:
            state.status = status  # type: ignore[assignment]
        state.version = (cast(Optional[int], state.version) or 0) + 1  # type: ignore[assignment]
        state.updated_at = datetime.utcnow()  # type: ignore[assignment]
        self.db.commit()
        self.db.refresh(state)
        return state

    def create_snapshot(
        self, project_id: str, stage_id: Optional[str] = None
    ) -> StateSnapshotModel:
        state = self.get_state(project_id)
        if state is None:
            raise ValueError(f"Project {project_id} not found")
        snapshot = StateSnapshotModel(
            project_id=project_id,
            state_json=cast(str, state.state_json),
            status=cast(str, state.status),
            stage_id=stage_id,
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def get_snapshots(self, project_id: str) -> List[StateSnapshotModel]:
        """查询指定项目的所有快照，按创建时间倒序排列。

        Args:
            project_id: 项目 ID。

        Returns:
            List[StateSnapshotModel]: 快照列表。
        """
        return (
            self.db.query(StateSnapshotModel)
            .filter(StateSnapshotModel.project_id == project_id)
            .order_by(StateSnapshotModel.created_at.desc())
            .all()
        )

    def rollback_to_snapshot(
        self, project_id: str, snapshot_id: int
    ) -> ProjectStateModel:
        """将项目状态回滚到指定快照。

        Args:
            project_id: 项目 ID。
            snapshot_id: 快照 ID。

        Returns:
            ProjectStateModel: 回滚后的项目状态。

        Raises:
            ValueError: 快照不存在时抛出。
        """
        snapshot = (
            self.db.query(StateSnapshotModel)
            .filter(
                StateSnapshotModel.id == snapshot_id,
                StateSnapshotModel.project_id == project_id,
            )
            .first()
        )
        if snapshot is None:
            raise ValueError(
                f"Snapshot {snapshot_id} not found for project {project_id}"
            )
        return self.update_state(
            project_id=project_id,
            state_json=cast(str, snapshot.state_json),
            status=cast(str, snapshot.status),
            skip_transition_check=True,
        )
