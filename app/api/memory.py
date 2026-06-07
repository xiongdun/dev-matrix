"""记忆系统 API 模块。"""

import logging
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.memory.manager import AgentMemoryManager, UserMemoryManager
from app.state.models import UserModel

logger = logging.getLogger(__name__)
router = APIRouter()


class MemoryItem(BaseModel):
    type: str
    key: str
    value: str
    source: str = "user_feedback"
    confidence: float = 1.0


class ProfileUpdate(BaseModel):
    preferences: dict[str, Any] | None = None
    patterns: dict[str, Any] | None = None


# ===== 用户记忆 =====


@router.get("/memories")
async def list_memories(
    memory_type: str | None = None,
    current_user: UserModel = Depends(get_current_user),
):
    """获取当前用户的记忆列表。"""
    mgr = UserMemoryManager(cast(int, current_user.id))
    memories = mgr.get_memories(memory_type)
    return {"memories": memories}


@router.post("/memories")
async def add_memory(
    item: MemoryItem,
    current_user: UserModel = Depends(get_current_user),
):
    """添加一条用户记忆。"""
    mgr = UserMemoryManager(cast(int, current_user.id))
    mgr.add_memory(
        memory_type=item.type,
        key=item.key,
        value=item.value,
        source=item.source,
        confidence=item.confidence,
    )
    return {"status": "ok"}


@router.delete("/memories/{key}")
async def remove_memory(
    key: str,
    current_user: UserModel = Depends(get_current_user),
):
    """删除指定 key 的记忆。"""
    mgr = UserMemoryManager(cast(int, current_user.id))
    removed = mgr.remove_memory(key)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Memory '{key}' not found")
    return {"status": "ok"}


@router.delete("/memories")
async def clear_memories(
    current_user: UserModel = Depends(get_current_user),
):
    """清空当前用户的所有记忆。"""
    mgr = UserMemoryManager(cast(int, current_user.id))
    mgr.clear_memories()
    return {"status": "ok"}


# ===== 用户画像 =====


@router.get("/profile")
async def get_profile(
    current_user: UserModel = Depends(get_current_user),
):
    """获取当前用户画像。"""
    mgr = UserMemoryManager(cast(int, current_user.id))
    return {"profile": mgr.get_profile()}


@router.put("/profile")
async def update_profile(
    updates: ProfileUpdate,
    current_user: UserModel = Depends(get_current_user),
):
    """更新当前用户画像。"""
    mgr = UserMemoryManager(cast(int, current_user.id))
    data = {}
    if updates.preferences:
        data["preferences"] = updates.preferences
    if updates.patterns:
        data["patterns"] = updates.patterns
    mgr.update_profile(data)
    return {"status": "ok"}


# ===== Agent 记忆（只读） =====


@router.get("/agents/{agent_role}/memory")
async def get_agent_memory(
    agent_role: str,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定 Agent 的共享记忆。"""
    mgr = AgentMemoryManager(agent_role)
    return {"memory": mgr.get_memory()}
