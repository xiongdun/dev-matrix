"""DevMatrix 应用程序主入口模块。

该模块负责初始化 FastAPI 应用程序、配置日志、设置中间件、
注册路由以及管理应用程序生命周期。

主要功能：
    - 结构化日志配置
    - 全局异常处理
    - 请求日志中间件
    - CORS 中间件配置
    - 数据库初始化
    - 技能自动发现与注册
    - API 路由注册

使用示例：
    直接运行该模块启动开发服务器：
    ```bash
    uvicorn app.main:app --reload
    ```

    或在其他模块中导入 app 实例：
    ```python
    from app.main import app
    ```

Attributes:
    app: FastAPI 应用程序实例。
    logger: 模块级日志记录器。
"""

import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import get_settings
from app.state.models import init_db
from app.api import (
    requirements,
    approvals,
    workflow,
    registry,
    workflow_config,
    workbench,
    events,
    lifecycle,
    workflow_instance,
    projects,
    settings as settings_api,
    scheduled_tasks,
    task_management,
    code_review,
    auth as auth_api,
    users as users_api,
    roles as roles_api,
    menus as menus_api,
    audit as audit_api,
)
from app.skills.registry import _global_registry as skill_registry
from app.skills.base import BaseSkill
from app.core.registry.discovery import discover_and_register
from app.middleware.audit import audit_middleware


class ErrorResponse(BaseModel):
    """标准错误响应模型。

    Attributes:
        detail: 错误详情描述。
        request_id: 关联的请求 ID，用于追踪。
    """

    detail: str
    request_id: str | None = None


def configure_logging() -> None:
    """配置应用日志。

    生产环境使用结构化 JSON 格式，自动脱敏敏感字段。
    """
    import re

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
                msg = re.sub(
                    rf'("{pattern}"\s*[:=]\s*"[^"]{3,}")',
                    lambda m: m.group(1)[:len(pattern)+4] + "***\"",
                    msg,
                    flags=re.IGNORECASE,
                )
            record.msg = msg
            return True

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
    root_logger.handlers = []
    root_logger.addHandler(handler)

    # 降低第三方库的日志噪音
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用程序生命周期。

    在启动时初始化数据库并完成技能发现，
    在关闭时记录关闭信息。

    Args:
        app: FastAPI 应用程序实例。
