"""事件类型模块。

定义 Event 数据类和 EventTypes 常量类。

主要类：
    - Event: 事件数据类。
    - EventTypes: 预定义事件类型常量。

使用示例：
    ```python
    from app.events.types import Event, EventTypes

    event = Event(
        type=EventTypes.WORKFLOW_STARTED,
        payload={"project_id": "1"},
        source="system"
    )
    ```
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Event:
    """事件数据类。

    Attributes:
        type: 事件类型字符串。
        payload: 事件载荷字典。
        timestamp: 事件时间戳，默认 UTC 当前时间。
        source: 事件来源，可选。
        project_id: 关联项目 ID，可选。
    """

    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str | None = None
    project_id: str | None = None


class EventTypes:
    """预定义事件类型常量。

    包含工作流、Agent、审批、状态等相关事件类型。
    """

    # 工作流事件
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Agent 事件
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    # 审批事件
    APPROVAL_REQUIRED = "approval.required"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"

    # 状态事件
    STATE_CHANGED = "state.changed"
    SNAPSHOT_CREATED = "snapshot.created"
    ROLLBACK_PERFORMED = "rollback.performed"
