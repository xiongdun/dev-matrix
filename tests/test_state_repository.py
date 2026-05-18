import pytest


class TestStateRepository:
    def test_get_state_not_found(self, state_repo):
        state = state_repo.get_state("nonexistent")
        assert state is None

    def test_update_state_create(self, state_repo, db_session):
        state = state_repo.update_state("proj-1", '{"key": "value"}', "pending")
        assert state.project_id == "proj-1"
        assert state.state_json == '{"key": "value"}'
        assert state.status == "pending"

        found = state_repo.get_state("proj-1")
        assert found is not None
        assert found.project_id == "proj-1"

    def test_update_state_update(self, state_repo, db_session):
        state_repo.update_state("proj-1", '{"version": 1}', "pending")
        updated = state_repo.update_state("proj-1", '{"version": 2}', "running")
        assert updated.state_json == '{"version": 2}'
        assert updated.status == "running"

        found = state_repo.get_state("proj-1")
        assert found.state_json == '{"version": 2}'
        assert found.status == "running"

    def test_create_snapshot(self, state_repo, db_session):
        state_repo.update_state("proj-1", '{"data": "test"}', "running")
        snapshot = state_repo.create_snapshot("proj-1")
        assert snapshot.project_id == "proj-1"
        assert snapshot.state_json == '{"data": "test"}'
        assert snapshot.status == "running"
        assert snapshot.id is not None

    def test_create_snapshot_not_found(self, state_repo):
        with pytest.raises(ValueError, match="Project nonexistent not found"):
            state_repo.create_snapshot("nonexistent")

    def test_get_snapshots(self, state_repo, db_session):
        state_repo.update_state("proj-1", '{"v": 1}', "running")
        snap1 = state_repo.create_snapshot("proj-1")
        state_repo.update_state("proj-1", '{"v": 2}', "completed")
        snap2 = state_repo.create_snapshot("proj-1")

        snapshots = state_repo.get_snapshots("proj-1")
        assert len(snapshots) == 2
        assert snapshots[0].id == snap2.id
        assert snapshots[1].id == snap1.id

    def test_get_snapshots_empty(self, state_repo):
        state_repo.update_state("proj-1", '{"v": 1}', "running")
        snapshots = state_repo.get_snapshots("proj-1")
        assert snapshots == []

    def test_rollback_to_snapshot(self, state_repo, db_session):
        state_repo.update_state("proj-1", '{"v": 1}', "running")
        snapshot = state_repo.create_snapshot("proj-1")
        state_repo.update_state("proj-1", '{"v": 2}', "completed")

        rolled = state_repo.rollback_to_snapshot("proj-1", snapshot.id)
        assert rolled.state_json == '{"v": 1}'
        assert rolled.status == "running"

        found = state_repo.get_state("proj-1")
        assert found.state_json == '{"v": 1}'
        assert found.status == "running"

    def test_rollback_to_snapshot_not_found(self, state_repo, db_session):
        state_repo.update_state("proj-1", '{"v": 1}', "running")
        with pytest.raises(
            ValueError, match="Snapshot 999 not found for project proj-1"
        ):
            state_repo.rollback_to_snapshot("proj-1", 999)

    def test_rollback_to_snapshot_wrong_project(self, state_repo, db_session):
        state_repo.update_state("proj-1", '{"v": 1}', "running")
        snapshot = state_repo.create_snapshot("proj-1")
        state_repo.update_state("proj-2", '{"v": 2}', "running")

        with pytest.raises(
            ValueError, match=f"Snapshot {snapshot.id} not found for project proj-2"
        ):
            state_repo.rollback_to_snapshot("proj-2", snapshot.id)
