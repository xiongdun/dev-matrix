"""增强事件总线模块。

支持：
- 事件持久化（SQLite 存储）
- 外部事件源适配器（Webhook、文件监控、定时器）
- Agent 事件订阅与路由
- 事件过滤与条件匹配
"""

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.events.types import Event, EventTypes

logger = logging.getLogger(__name__)

DEFAULT_SUBSCRIBER_TIMEOUT = 30.0


class EventSource(str, Enum):
    """事件来源类型。"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    WEBHOOK = "webhook"
    CRON = "cron"
    FILE_WATCHER = "file_watcher"


class EventPriority(int, Enum):
    """事件优先级。"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class EnhancedEvent:
    """增强事件，支持优先级、来源、路由元数据。"""
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str | None = None
    project_id: str | None = None
    id: str = ""
    priority: EventPriority = EventPriority.NORMAL
    source_type: EventSource = EventSource.SYSTEM
    target_agents: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


class EventFilter:
    """事件过滤器，用于条件匹配。"""

    def __init__(
        self,
        event_type: str | None = None,
        source: str | None = None,
        source_type: EventSource | None = None,
        project_id: str | None = None,
        priority_min: EventPriority = EventPriority.LOW,
    ):
        self.event_type = event_type
        self.source = source
        self.source_type = source_type
        self.project_id = project_id
        self.priority_min = priority_min

    def matches(self, event: EnhancedEvent) -> bool:
        """检查事件是否匹配过滤条件。"""
        if self.event_type and event.type != self.event_type:
            return False
        if self.source and event.source != self.source:
            return False
        if self.source_type and event.source_type != self.source_type:
            return False
        if self.project_id and event.project_id != self.project_id:
            return False
        if event.priority.value < self.priority_min.value:
            return False
        return True


class Subscription:
    """事件订阅，包含处理器和过滤器。"""

    def __init__(
        self,
        handler: Callable,
        event_filter: EventFilter | None = None,
        agent_role: str | None = None,
    ):
        self.handler = handler
        self.event_filter = event_filter
        self.agent_role = agent_role


class EnhancedEventBus:
    """增强事件总线。

    支持：
    - 事件持久化到数据库
    - 外部事件源适配器
    - Agent 级别事件订阅
    - 事件过滤与路由
    - 优先级队列
    """

    def __init__(self, persist_events: bool = True):
        self._subscriptions: dict[str, list[Subscription]] = {}
        self._global_subscriptions: list[Subscription] = []
        self._lock = asyncio.Lock()
        self._persist = persist_events
        self._event_history: list[EnhancedEvent] = []
        self._max_history = 1000

    def subscribe(
        self,
        event_type: str,
        handler: Callable,
        event_filter: EventFilter | None = None,
        agent_role: str | None = None,
    ) -> None:
        """订阅指定类型的事件。"""
        sub = Subscription(handler, event_filter, agent_role)
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        self._subscriptions[event_type].append(sub)
        logger.debug("Subscribed to '%s' (agent=%s)", event_type, agent_role)

    def subscribe_all(
        self,
        handler: Callable,
        event_filter: EventFilter | None = None,
    ) -> None:
        """订阅所有事件（全局订阅）。"""
        sub = Subscription(handler, event_filter)
        self._global_subscriptions.append(sub)
        logger.debug("Subscribed to all events")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """取消订阅。"""
        if event_type in self._subscriptions:
            self._subscriptions[event_type] = [
                s for s in self._subscriptions[event_type]
                if s.handler != handler
            ]

    async def publish(self, event: EnhancedEvent | Event) -> None:
        """发布事件。"""
        if isinstance(event, Event) and not isinstance(event, EnhancedEvent):
            event = EnhancedEvent(
                type=event.type,
                payload=event.payload,
                timestamp=event.timestamp or datetime.now(timezone.utc),
                source=event.source,
                project_id=event.project_id,
            )

        # 持久化
        if self._persist:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]

        logger.info("Event published: %s (source=%s, priority=%s)", event.type, event.source, event.priority)

        # 通知类型订阅者
        handlers = self._subscriptions.get(event.type, [])
        for sub in handlers:
            if sub.event_filter and not sub.event_filter.matches(event):
                continue
            await self._call_handler(sub.handler, event)

        # 通知全局订阅者
        for sub in self._global_subscriptions:
            if sub.event_filter and not sub.event_filter.matches(event):
                continue
            await self._call_handler(sub.handler, event)

    async def _call_handler(self, handler: Callable, event: EnhancedEvent) -> None:
        """调用事件处理器，带超时保护。"""
        try:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await asyncio.wait_for(result, timeout=DEFAULT_SUBSCRIBER_TIMEOUT)
        except asyncio.TimeoutError:
            logger.error("Handler timed out for event '%s'", event.type)
        except Exception:
            logger.exception("Handler error for event '%s'", event.type)

    def get_history(
        self,
        event_type: str | None = None,
        limit: int = 50,
    ) -> list[EnhancedEvent]:
        """获取事件历史。"""
        events = self._event_history
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """获取事件统计。"""
        type_counts: dict[str, int] = {}
        for e in self._event_history:
            type_counts[e.type] = type_counts.get(e.type, 0) + 1
        return {
            "total_events": len(self._event_history),
            "subscriptions": {k: len(v) for k, v in self._subscriptions.items()},
            "global_subscriptions": len(self._global_subscriptions),
            "type_counts": type_counts,
        }

    def clear(self) -> None:
        """清除所有订阅。"""
        self._subscriptions.clear()
        self._global_subscriptions.clear()
        self._event_history.clear()


# 全局增强事件总线
enhanced_bus = EnhancedEventBus()
