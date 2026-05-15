"""SSE 事件推送 API 模块。

提供 Server-Sent Events 端点，实时推送审批通知到前端。
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.events.bus import event_bus
from app.events.types import EventTypes

logger = logging.getLogger(__name__)
router = APIRouter()


class SSESubscriber:
    def __init__(self, role: Optional[str] = None):
        self.role = role
        self._queue = asyncio.Queue()

    async def put(self, data: dict):
        await self._queue.put(data)

    async def get(self, timeout: float = 30.0):
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None


_subscribers: list[SSESubscriber] = []


def _on_event(event):
    payload = {
        "type": event.type,
        "payload": event.payload,
        "project_id": event.project_id,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
    }
    for sub in _subscribers:
        if sub.role and event.payload:
            event_role = event.payload.get("agent_role", "")
            if event_role and sub.role != event_role:
                continue
        asyncio.get_event_loop().create_task(sub.put(payload))


_bus_listener_attached = False


def _ensure_listener():
    global _bus_listener_attached
    if not _bus_listener_attached:
        for event_type in [
            EventTypes.WORKFLOW_STARTED,
            EventTypes.WORKFLOW_COMPLETED,
            EventTypes.WORKFLOW_FAILED,
            EventTypes.AGENT_STARTED,
            EventTypes.AGENT_COMPLETED,
            EventTypes.AGENT_FAILED,
            EventTypes.APPROVAL_REQUIRED,
            EventTypes.APPROVAL_APPROVED,
            EventTypes.APPROVAL_REJECTED,
            EventTypes.STATE_CHANGED,
        ]:
            event_bus.subscribe(event_type, _on_event)
        _bus_listener_attached = True


@router.get("/stream")
async def event_stream(
    role: Optional[str] = Query(None, max_length=64),
):
    _ensure_listener()
    subscriber = SSESubscriber(role=role)
    _subscribers.append(subscriber)

    async def generate():
        try:
            while True:
                data = await subscriber.get(timeout=30.0)
                if data:
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                else:
                    yield f": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if subscriber in _subscribers:
                _subscribers.remove(subscriber)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
