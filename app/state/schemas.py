from datetime import datetime
from typing import Optional, Any, Dict

from pydantic import BaseModel, ConfigDict


class ProjectStateBase(BaseModel):
    project_id: str
    state_json: Optional[str] = "{}"
    status: Optional[str] = "pending"


class ProjectStateCreate(ProjectStateBase):
    pass


class ProjectState(ProjectStateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StateSnapshot(BaseModel):
    id: int
    project_id: str
    state_json: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
