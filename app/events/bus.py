"""事件总线模块。

提供 EventBus 类，实现发布-订阅模式的事件系统。
支持同步和异步事件处理器，带超时保护。

主要类：
    - EventBus: 事件总线，管理事件的订阅、取消订阅和发布。
    - event_bus: 全局事件总线实例。

使用示例：
    ```python
    from app.events.bus import event_bus
    from app.events.types import Event

    def handler(event):
        print(event.payload)

    event_bus.subscribe("workflow.started", handler)
    await event_bus.publish(Event(type="workflow.started", payload={"id": "1"}))
    ```
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from app.events.types import Event

logger = logging.getLogger(__name__)

# 订阅者执行默认超时时间（秒）
DEFAULT_SUBSCRIBER_TIMEOUT = 30.0


class EventBus:
    """事件总线，实现发布-订阅模式。

    支持同步和异步事件处理器，带超时保护。

    Attributes:
        _handlers: 事件类型到处理器列表的映射。
        _lock: 异步锁，保护处理器注册操作。

    Example:
        ```python
        bus = EventBus()
        bus.subscribe("my_event", lambda e: print(e.payload))
        await bus.publish(Event(type="my_event", payload={"key": "value"}))
        ```
    """

    def __init__(self):
        """初始化事件总线。"""
        self._handlers: dict[str, list[Callable[[Event], Any]]] = {}
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """订阅指定类型的事件。

        Args:
            event_type: 事件类型字符串。
            handler: 事件处理器函数。
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug("Subscribed handler to event type '%s'", event_type)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """取消订阅指定类型的事件。

        Args:
            event_type: 事件类型字符串。
            handler: 要移除的处理器函数。
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug("Unsubscribed handler from event type '%s'", event_type)
            except ValueError:
                pass

    async def publish(self, event: Event) -> None:
        """发布事件到所有订阅者。

        同步处理器直接调用，异步处理器使用 wait_for 超时保护。

        Args:
            event: 要发布的事件实例。
        """
        handlers = self._handlers.get(event.type, [])
        if not handlers:
            logger.debug("No handlers for event type '%s'", event.type)
            return

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await asyncio.wait_for(result, timeout=DEFAULT_SUBSCRIBER_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error(
                    "Subscriber handler for event '%s' timed out after %.1fs",
                    event.type,
                    DEFAULT_SUBSCRIBER_TIMEOUT,
                )
            except Exception:
                logger.exception(
                    "Subscriber handler for event '%s' raised an exception",
                    event.type,
                )

    def clear(self) -> None:
        """清除所有事件处理器。"""
        self._handlers.clear()
        logger.debug("Cleared all event handlers")


# 全局事件总线实例
event_bus = EventBus()
