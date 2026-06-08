"""Agent 消息总线 API 模块。"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.events.message_bus import AgentMessage, MessageType, agent_bus
from app.state.models import UserModel

logger = logging.getLogger(__name__)
router = APIRouter()


class SendMessageRequest(BaseModel):
    to_agent: str
    subject: str
    content: str
    message_type: str = "notification"
    payload: dict[str, Any] = {}
    project_id: str | None = None


class SetContextRequest(BaseModel):
    key: str
    value: Any
    project_id: str | None = None


@router.post("/send")
async def send_message(
    payload: SendMessageRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """发送消息到指定 Agent。"""
    msg = AgentMessage(
        from_agent="user",
        to_agent=payload.to_agent,
        message_type=MessageType(payload.message_type),
        subject=payload.subject,
        content=payload.content,
        payload=payload.payload,
        project_id=payload.project_id,
    )
    msg_id = await agent_bus.send(msg)
    return {"status": "ok", "message_id": msg_id}


@router.get("/messages")
async def get_messages(
    agent_role: str | None = None,
    project_id: str | None = None,
    limit: int = 50,
    current_user: UserModel = Depends(get_current_user),
):
    """获取消息历史。"""
    messages = agent_bus.get_messages(agent_role=agent_role, project_id=project_id, limit=limit)
    return {
        "messages": [
            {
                "id": m.id,
                "from": m.from_agent,
                "to": m.to_agent,
                "type": m.message_type.value,
                "subject": m.subject,
                "content": m.content,
                "status": m.status.value,
                "timestamp": m.timestamp.isoformat(),
                "project_id": m.project_id,
            }
            for m in messages
        ]
    }


@router.get("/context")
async def get_context(
    project_id: str | None = None,
    current_user: UserModel = Depends(get_current_user),
):
    """获取共享上下文。"""
    return {"context": agent_bus.get_all_context(project_id=project_id)}


@router.post("/context")
async def set_context(
    payload: SetContextRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """设置共享上下文。"""
    agent_bus.set_context(
        key=payload.key,
        value=payload.value,
        updated_by=current_user.username,
        project_id=payload.project_id,
    )
    return {"status": "ok"}


@router.delete("/context/{key}")
async def delete_context(
    key: str,
    current_user: UserModel = Depends(get_current_user),
):
    """删除共享上下文。"""
    if not agent_bus.delete_context(key):
        raise HTTPException(status_code=404, detail=f"Context '{key}' not found")
    return {"status": "ok"}


@router.get("/stats")
async def get_stats(
    current_user: UserModel = Depends(get_current_user),
):
    """获取消息总线统计。"""
    return agent_bus.get_stats()
