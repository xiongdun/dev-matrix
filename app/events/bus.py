import asyncio
from typing import Any, Callable, Dict, List, Optional

from app.events.types import Event


class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[Callable[[Event], Any]]] = {}
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass

    async def publish(self, event: Event) -> None:
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass

    def clear(self) -> None:
        self._handlers.clear()


event_bus = EventBus()
