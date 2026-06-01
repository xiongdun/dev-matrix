"""健康检查 API 模块。

提供应用和依赖服务的健康状态检查端点。
- /health/live — 存活探针（应用是否运行）
- /health/ready — 就绪探针（依赖服务是否可用）
- /health — 综合健康状态
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.state.models import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


class HealthCheck(BaseModel):
    """健康检查结果模型。"""

    status: str
    checks: dict[str, str]


class HealthResponse(BaseModel):
    """健康检查响应模型。"""

    status: str
    version: str = "0.1.0"
    checks: dict[str, dict[str, str]]


def _check_database() -> tuple:
    """检查数据库连接。

    Returns:
        tuple: (是否健康, 状态信息)
    """
    try:
        db: Session = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        return True, "connected"
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        return False, f"error: {exc}"


def _check_temporal() -> tuple:
    """检查 Temporal 连接。

    Returns:
        tuple: (是否健康, 状态信息)
    """
    try:
        from app.config import get_settings

        settings = get_settings()
        if not settings.temporal_host:
            return True, "not configured"

        import socket

        host, port = settings.temporal_host.split(":")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, int(port)))
        sock.close()

        if result == 0:
            return True, "connected"
        return False, f"unreachable (code: {result})"
    except Exception as exc:
        logger.warning("Temporal health check failed: %s", exc)
        return False, f"error: {exc}"


def _check_redis() -> tuple:
    """检查 Redis 连接。

    Returns:
        tuple: (是否健康, 状态信息)
    """
    try:
        from app.config import get_settings

        settings = get_settings()
        if not settings.redis_url:
            return True, "not configured"

        import redis

        r = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        r.ping()
        return True, "connected"
    except ImportError:
        return True, "redis client not installed"
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        return False, f"error: {exc}"


@router.get("/health/live", response_model=HealthCheck)
async def liveness_check():
    """存活探针。

    检查应用本身是否正常运行。
    Kubernetes 使用此端点决定是否需要重启容器。
    """
    return HealthCheck(
        status="healthy",
        checks={"app": "running"},
    )


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check():
    """就绪探针。

    检查应用及其依赖服务是否可用。
    Kubernetes 使用此端点决定是否将流量路由到该容器。
    """
    checks = {}

    # 数据库检查
    db_ok, db_status = _check_database()
    checks["database"] = {"status": "healthy" if db_ok else "unhealthy", "detail": db_status}

    # Temporal 检查
    temporal_ok, temporal_status = _check_temporal()
    checks["temporal"] = {
        "status": "healthy" if temporal_ok else "unhealthy",
        "detail": temporal_status,
    }

    # Redis 检查
    redis_ok, redis_status = _check_redis()
    checks["redis"] = {"status": "healthy" if redis_ok else "unhealthy", "detail": redis_status}

    all_healthy = all(
        check["status"] == "healthy" or check["detail"] == "not configured"
        for check in checks.values()
    )

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        checks=checks,
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """综合健康检查。

    返回应用及所有依赖服务的健康状态。
    """
    return await readiness_check()
