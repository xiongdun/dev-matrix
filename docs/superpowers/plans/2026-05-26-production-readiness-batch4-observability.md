# 批次 4：可观测性实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提升系统可观测性，包括结构化日志、审计日志集成到数据库、请求链路追踪完善。

**Architecture:** 使用 Python 标准 logging 的 JSON 格式化替代 structlog（减少依赖）；通过 FastAPI 中间件自动记录所有写操作审计日志；完善 request_id 在日志和错误响应中的传递。

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy, standard logging

---

## 文件变更总览

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/utils/audit.py` | 修改 | 完善数据库写入，集成到 API |
| `app/state/models.py` | 修改 | 新增 AuditLogModel 数据库模型 |
| `app/main.py` | 修改 | 改进日志格式，添加敏感字段脱敏 |
| `app/api/audit.py` | 创建 | 审计日志查询 API |
| `app/middleware/audit.py` | 创建 | 自动审计日志中间件 |
| `tests/test_audit.py` | 创建 | 审计日志测试 |

---

## Task 1: 审计日志数据库模型与集成

**Files:**
- Modify: `app/state/models.py`
- Modify: `app/utils/audit.py`
- Create: `app/api/audit.py`

**背景:** 当前审计日志只写入文件，`_write_to_db` 是空实现，无法通过 API 查询。

- [ ] **Step 1: 新增审计日志数据库模型**

修改 `app/state/models.py`，添加：

```python
class AuditLogModel(Base):
    """审计日志数据库模型。

    记录系统中所有重要的用户操作和系统事件。
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    action = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    resource_type = Column(String(50), nullable=True)  # 资源类型：user, role, workflow 等
    resource_id = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)  # JSON 格式的详细信息
    status = Column(String(20), default="success")  # success / failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("UserModel", backref="audit_logs")
```

- [ ] **Step 2: 完善审计日志工具类**

修改 `app/utils/audit.py`：

```python
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
```

- [ ] **Step 3: 创建审计日志查询 API**

创建 `app/api/audit.py`：

```python
"""审计日志 API 模块。

提供审计日志的查询和管理接口。
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.state.models import get_db, AuditLogModel
from app.api.deps import get_current_user, require_permission
from app.utils.audit import AuditLogger

router = APIRouter(prefix="/api/audit", tags=["audit"])
audit_logger = AuditLogger()


class AuditLogResponse(BaseModel):
    id: int
    action: str
    username: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    total: int
    items: list[AuditLogResponse]


@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    action: Optional[str] = Query(None, description="按操作类型筛选"),
    user_id: Optional[int] = Query(None, description="按用户 ID 筛选"),
    resource_type: Optional[str] = Query(None, description="按资源类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始时间"),
    end_date: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user = Depends(require_permission("audit:read")),
):
    """查询审计日志列表。

    需要 audit:read 权限。
    """
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
        items=[AuditLogResponse.from_orm(log) for log in logs],
    )
```

- [ ] **Step 4: Commit**

```bash
git add app/state/models.py app/utils/audit.py app/api/audit.py
git commit -m "observability: add audit log database model and query API"
```

---

## Task 2: 自动审计日志中间件

**Files:**
- Create: `app/middleware/audit.py`
- Modify: `app/main.py`

**背景:** 当前需要手动在每个 API 中调用 `log_audit`，容易遗漏。

- [ ] **Step 1: 创建自动审计中间件**

创建 `app/middleware/audit.py`：

```python
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
        from app.api.deps import get_current_user
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
```

- [ ] **Step 2: 在 main.py 中注册中间件**

修改 `app/main.py`：

```python
from app.middleware.audit import audit_middleware

# 注册审计中间件（在请求日志中间件之后）
app.middleware("http")(audit_middleware)
```

- [ ] **Step 3: Commit**

```bash
git add app/middleware/audit.py app/main.py
git commit -m "observability: add automatic audit logging middleware"
```

---

## Task 3: 日志敏感字段脱敏

**Files:**
- Modify: `app/main.py`

**背景:** 当前日志可能记录敏感信息（密码、Token、API Key）。

- [ ] **Step 1: 改进日志配置添加脱敏**

修改 `app/main.py` 的 `configure_logging`：

```python
def configure_logging() -> None:
    """配置应用日志。

    生产环境使用结构化 JSON 格式，自动脱敏敏感字段。
    """
    import sys
    import json
    import logging

    settings = get_settings()
    log_level = logging.DEBUG if settings.debug else logging.INFO

    class SensitiveDataFilter(logging.Filter):
        """日志敏感数据过滤器。"""

        SENSITIVE_PATTERNS = [
            "password", "token", "secret", "api_key", "private_key",
            "authorization", "cookie", "set-cookie",
        ]

        def filter(self, record: logging.LogRecord) -> bool:
            if not hasattr(record, "msg"):
                return True

            msg = str(record.msg)
            for pattern in self.SENSITIVE_PATTERNS:
                # 简单的字符串替换脱敏
                import re
                msg = re.sub(
                    rf'("{pattern}"\s*[:=]\s*"[^"]{{3,}}")',
                    lambda m: m.group(1)[:len(pattern)+4] + "***\"",
                    msg,
                    flags=re.IGNORECASE,
                )
            record.msg = msg
            return True

    # JSON 格式化器（生产环境）
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "request_id": getattr(record, "request_id", None),
            }
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_data, ensure_ascii=False)

    handler = logging.StreamHandler(sys.stdout)

    if settings.debug:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        formatter = JsonFormatter()

    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # 降低第三方库日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

- [ ] **Step 2: Commit**

```bash
git add app/main.py
git commit -m "observability: add sensitive data masking in logs"
```

---

## 批次 4 验收检查

- [ ] 所有 POST/PUT/DELETE 操作自动记录审计日志到数据库
- [ ] 审计日志 API `/api/audit/logs` 可查询日志列表
- [ ] 日志中密码、Token 等敏感字段显示为 `***`
- [ ] 生产环境日志输出 JSON 格式
- [ ] 日志包含 request_id 字段
