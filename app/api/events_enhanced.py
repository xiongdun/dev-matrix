"""事件系统 API 模块。

提供事件历史查询、订阅管理、Webhook 接收等端点。
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.events.agent_router import agent_router
from app.events.enhanced_bus import EnhancedEvent, enhanced_bus
from app.state.models import UserModel

logger = logging.getLogger(__name__)
router = APIRouter()


class EventHistoryResponse(BaseModel):
    events: list[dict[str, Any]]
    total: int


class SubscriptionInfo(BaseModel):
    agent_role: str
    event_types: list[str]


@router.get("/history", response_model=EventHistoryResponse)
async def get_event_history(
    event_type: str | None = None,
    limit: int = 50,
    current_user: UserModel = Depends(get_current_user),
):
    """获取事件历史。"""
    events = enhanced_bus.get_history(event_type=event_type, limit=limit)
    return EventHistoryResponse(
        events=[
            {
                "id": e.id,
                "type": e.type,
                "source": e.source,
                "source_type": e.source_type.value if e.source_type else None,
                "priority": e.priority.value if e.priority else 1,
                "project_id": e.project_id,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "payload_keys": list(e.payload.keys()) if e.payload else [],
            }
            for e in events
        ],
        total=len(events),
    )


@router.get("/stats")
async def get_event_stats(
    current_user: UserModel = Depends(get_current_user),
):
    """获取事件统计。"""
    return enhanced_bus.get_stats()


@router.get("/subscriptions")
async def get_subscriptions(
    current_user: UserModel = Depends(get_current_user),
):
    """获取所有 Agent 的事件订阅。"""
    return {"subscriptions": agent_router.get_all_subscriptions()}


@router.post("/publish")
async def publish_event(
    event_type: str,
    payload: dict[str, Any] = {},
    source: str = "manual",
    current_user: UserModel = Depends(get_current_user),
):
    """手动发布事件（调试用）。"""
    event = EnhancedEvent(
        type=event_type,
        payload=payload,
        source=source,
    )
    await enhanced_bus.publish(event)
    return {"status": "ok", "event_id": event.id}
