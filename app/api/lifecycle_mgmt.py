"""Agent 生命周期管理 API 模块。"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.lifecycle.manager import AgentState, ResourceLimits, lifecycle_manager
from app.state.models import UserModel

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateInstanceRequest(BaseModel):
    agent_role: str
    max_tokens: int = 100000
    max_duration_seconds: int = 3600
    max_concurrent_tasks: int = 3


@router.get("/instances")
async def list_instances(
    agent_role: str | None = None,
    current_user: UserModel = Depends(get_current_user),
):
    """列出所有 Agent 实例。"""
    state = AgentState(agent_role) if agent_role else None
    instances = lifecycle_manager.list_instances(agent_role=agent_role)
    return {"instances": [i.to_dict() for i in instances]}


@router.get("/instances/{instance_id}")
async def get_instance(
    instance_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """获取 Agent 实例详情。"""
    instance = lifecycle_manager.get_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return {"instance": instance.to_dict()}


@router.post("/instances")
async def create_instance(
    payload: CreateInstanceRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """创建 Agent 实例。"""
    limits = ResourceLimits(
        max_tokens=payload.max_tokens,
        max_duration_seconds=payload.max_duration_seconds,
        max_concurrent_tasks=payload.max_concurrent_tasks,
    )
    instance = lifecycle_manager.create_instance(payload.agent_role, limits)
    await lifecycle_manager.start(instance.id)
    return {"instance": instance.to_dict()}


@router.post("/instances/{instance_id}/pause")
async def pause_instance(
    instance_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """暂停 Agent 实例。"""
    success = await lifecycle_manager.pause(instance_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause instance")
    return {"status": "ok"}


@router.post("/instances/{instance_id}/resume")
async def resume_instance(
    instance_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """恢复 Agent 实例。"""
    success = await lifecycle_manager.resume(instance_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume instance")
    return {"status": "ok"}


@router.delete("/instances/{instance_id}")
async def destroy_instance(
    instance_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """销毁 Agent 实例。"""
    success = await lifecycle_manager.destroy(instance_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot destroy instance")
    return {"status": "ok"}


@router.get("/stats")
async def get_stats(
    current_user: UserModel = Depends(get_current_user),
):
    """获取生命周期统计。"""
    return lifecycle_manager.get_stats()
