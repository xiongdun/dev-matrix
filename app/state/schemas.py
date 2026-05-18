"""Pydantic 模式模块。

定义项目状态和快照的数据传输对象（DTO）。

主要类：
    - ProjectStateBase: 项目状态基础模式。
    - ProjectStateCreate: 项目状态创建模式。
    - ProjectState: 项目状态完整模式。
    - StateSnapshot: 状态快照模式。

使用示例：
    ```python
    from app.state.schemas import ProjectStateCreate

    data = ProjectStateCreate(project_id="proj_1", state_json="{}", status="pending")
    ```
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProjectStateBase(BaseModel):
    """项目状态基础模式。

    Attributes:
        project_id: 项目 ID。
        state_json: 状态 JSON 字符串。
        status: 状态标识。
    """

    project_id: str
    state_json: Optional[str] = "{}"
    status: Optional[str] = "pending"


class ProjectStateCreate(ProjectStateBase):
    """项目状态创建模式，继承自 ProjectStateBase，无额外字段。"""

    pass


class ProjectState(ProjectStateBase):
    """项目状态完整模式，包含数据库字段。

    Attributes:
        id: 数据库主键。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StateSnapshot(BaseModel):
    """状态快照模式。

    Attributes:
        id: 快照主键。
        project_id: 项目 ID。
        state_json: 快照时的状态 JSON。
        status: 快照时的状态标识。
        created_at: 快照创建时间。
    """

    id: int
    project_id: str
    state_json: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
