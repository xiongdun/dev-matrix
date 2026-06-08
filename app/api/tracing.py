"""执行追踪 API 模块。"""

import logging
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.state.models import UserModel
from app.tracing.tracer import tracer

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/traces")
async def list_traces(
    limit: int = 20,
    current_user: UserModel = Depends(get_current_user),
):
    """获取最近的追踪记录。"""
    traces = tracer.get_recent_traces(limit=limit)
    return {"traces": [t.to_dict() for t in traces]}


@router.get("/traces/{trace_id}")
async def get_trace(
    trace_id: str,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定追踪的详细信息。"""
    trace = tracer.get_trace(trace_id)
    if not trace:
        return {"error": "Trace not found"}
    return {"trace": trace.to_dict()}


@router.get("/stats")
async def get_tracing_stats(
    current_user: UserModel = Depends(get_current_user),
):
    """获取追踪统计。"""
    return tracer.get_stats()
