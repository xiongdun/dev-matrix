"""审计日志模块。

提供审计日志记录功能，支持文件和数据库两种输出方式。
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.state.models import AuditLogModel

logger = logging.getLogger(__name__)


@dataclass
class AuditLog:
    """审计日志数据类。"""
    action: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    status: str = "success"
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """审计日志记录器。"""

    def __init__(self, log_file: Optional[str] = None, use_db: bool = True):
        self.log_file = Path(log_file) if log_file else Path("logs/audit.log")
        self.use_db = use_db
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        db: Session,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            action=action,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            status=status,
            error_message=error_message,
        )

        # 写入文件
        self._write_to_file(audit_log)

        # 写入数据库
        if self.use_db and db:
            self._write_to_db(db, audit_log)

        return audit_log

    def _write_to_file(self, audit_log: AuditLog):
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(audit_log.to_json() + "\n")
        except Exception as exc:
            logger.error("Failed to write audit log to file: %s", exc)

    def _write_to_db(self, db: Session, audit_log: AuditLog):
        try:
            db_log = AuditLogModel(
                action=audit_log.action,
                user_id=audit_log.user_id,
                username=audit_log.username,
                ip_address=audit_log.ip_address,
                user_agent=audit_log.user_agent,
                resource_type=audit_log.resource_type,
                resource_id=audit_log.resource_id,
                details=json.dumps(audit_log.details, ensure_ascii=False) if audit_log.details else None,
                status=audit_log.status,
                error_message=audit_log.error_message,
            )
            db.add(db_log)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("Failed to write audit log to database: %s", exc)

    def get_logs(
        self,
        db: Session,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple:
        query = db.query(AuditLogModel)

        if action:
            query = query.filter(AuditLogModel.action == action)
        if user_id:
            query = query.filter(AuditLogModel.user_id == user_id)
        if resource_type:
            query = query.filter(AuditLogModel.resource_type == resource_type)
        if start_date:
            query = query.filter(AuditLogModel.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLogModel.created_at <= end_date)

        total = query.count()
        logs = query.order_by(AuditLogModel.created_at.desc()).offset(offset).limit(limit).all()
        return total, logs


# 全局审计日志记录器实例
_default_logger = AuditLogger()


def log_audit(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    **kwargs
) -> AuditLog:
    """便捷函数，使用默认记录器记录审计日志。"""
    return _default_logger.log(db, action, user_id=user_id, username=username, **kwargs)
