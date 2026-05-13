import json
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

Base = declarative_base()


class ProjectStateModel(Base):
    __tablename__ = "project_states"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), unique=True, index=True, nullable=False)
    state_json = Column(Text, default="{}")
    status = Column(String(32), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StateSnapshotModel(Base):
    __tablename__ = "state_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    state_json = Column(Text, default="{}")
    status = Column(String(32), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


@event.listens_for(ProjectStateModel, "before_update")
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False}
            if settings.database_url.startswith("sqlite")
            else {},
        )
    return _engine


def get_session_maker():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def init_db():
    Base.metadata.create_all(bind=get_engine())


def get_db():
    Session = get_session_maker()
    db = Session()
    try:
        yield db
    finally:
        db.close()
