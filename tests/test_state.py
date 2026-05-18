import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.state.models import Base
from app.state.repository import StateRepository


class TestStateRepository:
    @pytest.fixture
    def db(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    @pytest.fixture
    def repo(self, db):
        return StateRepository(db)

    def test_create_and_get_state(self, repo):
        state = repo.update_state("proj-1", '{"key": "value"}', "pending")
        assert state.project_id == "proj-1"

        found = repo.get_state("proj-1")
        assert found is not None
        assert found.status == "pending"

    def test_create_snapshot(self, repo):
        repo.update_state("proj-1", '{"version": 1}', "running")
        snapshot = repo.create_snapshot("proj-1")
        assert snapshot.project_id == "proj-1"
        assert snapshot.status == "running"

    def test_get_snapshots(self, repo):
        repo.update_state("proj-1", '{"v": 1}', "running")
        repo.create_snapshot("proj-1")
        repo.create_snapshot("proj-1")

        snapshots = repo.get_snapshots("proj-1")
        assert len(snapshots) == 2

    def test_rollback(self, repo):
        repo.update_state("proj-1", '{"v": 1}', "running")
        snapshot = repo.create_snapshot("proj-1")
        repo.update_state("proj-1", '{"v": 2}', "completed")

        rolled = repo.rollback_to_snapshot("proj-1", snapshot.id)
        assert rolled.status == "running"
