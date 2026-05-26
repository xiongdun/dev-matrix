"""自动审计日志中间件。

自动记录所有 POST/PUT/DELETE 请求的审计日志。
"""

import json
import logging
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.state.models import get_db
from app.utils.audit import AuditLogger

logger = logging.getLogger(__name__)
audit_logger = AuditLogger()

# 敏感字段，记录时脱敏
SENSITIVE_FIELDS = {"password", "token", "secret", "api_key", "private_key"}


def _mask_sensitive_data(data: dict) -> dict:
    """脱敏敏感字段。"""
    if not isinstance(data, dict):
        return data
    masked = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            masked[key] = "***"
        elif isinstance(value, dict):
            masked[key] = _mask_sensitive_data(value)
        elif isinstance(value, list):
            masked[key] = [_mask_sensitive_data(item) if isinstance(item, dict) else item for item in value]
        else:
            masked[key] = value
    return masked


async def audit_middleware(request: Request, call_next):
    """自动审计日志中间件。

    记录所有写操作（POST/PUT/DELETE）的审计日志。
    """
    method = request.method
    path = request.url.path

    # 只记录写操作
    if method not in ("POST", "PUT", "DELETE", "PATCH"):
        return await call_next(request)

    # 跳过健康检查和审计日志自身
    if path.startswith("/health") or path.startswith("/api/audit"):
        return await call_next(request)

    # 获取用户信息
    user_id: Optional[int] = None
    username: Optional[str] = None
    try:
        from app.api.auth import get_current_user
        db: Session = next(get_db())
        user = await get_current_user(request, db)
        user_id = user.id
        username = user.username
    except Exception:
        pass

    # 获取请求体（有限制大小）
    details = None
    try:
        body = await request.body()
        if body and len(body) < 10000:  # 限制 10KB
            body_json = json.loads(body)
            details = _mask_sensitive_data(body_json)
    except Exception:
        pass

    # 执行请求
    response = await call_next(request)

    # 记录审计日志
    try:
        db: Session = next(get_db())
        resource_type = _extract_resource_type(path)
        resource_id = _extract_resource_id(path)

        audit_logger.log(
            db=db,
            action=f"{method.lower()}_{resource_type}",
            user_id=user_id,
            username=username,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            status="success" if response.status_code < 400 else "failed",
        )
    except Exception as exc:
        logger.error("Failed to record audit log: %s", exc)

    return response


def _extract_resource_type(path: str) -> str:
    """从路径提取资源类型。"""
    parts = path.strip("/").split("/")
    if len(parts) >= 2:
        return parts[1]  # api/users -> users
    return "unknown"


def _extract_resource_id(path: str) -> Optional[str]:
    """从路径提取资源 ID。"""
    parts = path.strip("/").split("/")
    if len(parts) >= 3:
        return parts[2]
    return None
