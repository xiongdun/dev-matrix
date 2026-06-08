"""可观测性 API 模块。"""

import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.observability.metrics import metrics
from app.state.models import UserModel

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    current_user: UserModel = Depends(get_current_user),
):
    """获取 Dashboard 数据。"""
    return metrics.get_dashboard_data()


@router.get("/tokens")
async def get_token_metrics(
    current_user: UserModel = Depends(get_current_user),
):
    """获取 Token 消耗指标。"""
    tm = metrics.get_token_metrics()
    return {
        "total_tokens": tm.total_tokens,
        "input_tokens": tm.total_input_tokens,
        "output_tokens": tm.total_output_tokens,
        "total_cost": round(tm.total_cost, 4),
        "by_agent": tm.by_agent,
        "by_sdk": tm.by_sdk,
        "by_model": tm.by_model,
    }


@router.get("/performance")
async def get_performance(
    current_user: UserModel = Depends(get_current_user),
):
    """获取性能指标。"""
    pm = metrics.get_performance_metrics()
    return {
        "total_requests": pm.total_requests,
        "successful_requests": pm.successful_requests,
        "failed_requests": pm.failed_requests,
        "avg_response_time_ms": round(pm.avg_response_time_ms, 2),
        "p95_response_time_ms": round(pm.p95_response_time_ms, 2),
        "p99_response_time_ms": round(pm.p99_response_time_ms, 2),
    }


@router.get("/costs")
async def get_costs(
    days: int = 7,
    current_user: UserModel = Depends(get_current_user),
):
    """获取成本报表。"""
    return {
        "daily_costs": metrics.get_daily_costs(days),
        "total_cost": round(metrics.get_token_metrics().total_cost, 4),
    }
