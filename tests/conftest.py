import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.state.models import Base
from app.state.repository import StateRepository
from app.events.bus import EventBus


@pytest.fixture
def event_bus():
    bus = EventBus()
    yield bus
    bus.clear()


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def state_repo(db_session):
    return StateRepository(db_session)


class MockLLMRouter:
    def __init__(self):
        self.name = "mock"

    async def complete(self, prompt, **kwargs):
        return "mock response"

    async def chat(self, messages, **kwargs):
        return "mock chat response"


@pytest.fixture
def mock_llm_router():
    return MockLLMRouter()
