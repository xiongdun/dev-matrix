"""审计日志 API 模块。

提供审计日志的查询和管理接口。
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.state.models import get_db
from app.utils.audit import AuditLogger

router = APIRouter(prefix="/api/audit", tags=["audit"])
audit_logger = AuditLogger()


class AuditLogResponse(BaseModel):
    id: int
    action: str
    username: str | None
    resource_type: str | None
    resource_id: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    total: int
    items: list[AuditLogResponse]


@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    action: str | None = Query(None, description="按操作类型筛选"),
    user_id: int | None = Query(None, description="按用户 ID 筛选"),
    resource_type: str | None = Query(None, description="按资源类型筛选"),
    start_date: datetime | None = Query(None, description="开始时间"),
    end_date: datetime | None = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """查询审计日志列表。"""
    total, logs = audit_logger.get_logs(
        db=db,
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return AuditLogListResponse(
        total=total,
        items=[AuditLogResponse.model_validate(log) for log in logs],
    )
