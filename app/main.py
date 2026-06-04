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

import json
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import (
    approvals,
    code_review,
    events,
    lifecycle,
    projects,
    registry,
    requirements,
    scheduled_tasks,
    task_management,
    workbench,
    workflow,
    workflow_config,
    workflow_instance,
)
from app.api import (
    audit as audit_api,
)
from app.api import (
    auth as auth_api,
)
from app.api import (
    health as health_api,
)
from app.api import (
    menus as menus_api,
)
from app.api import (
    roles as roles_api,
)
from app.api import (
    settings as settings_api,
)
from app.api import (
    users as users_api,
)
from app.config import get_settings
from app.core.limiter import limiter
from app.core.registry.discovery import discover_and_register
from app.middleware.audit import audit_middleware
from app.skills.base import BaseSkill
from app.skills.registry import _global_registry as skill_registry
from app.state.models import init_db


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
            "password",
            "token",
            "secret",
            "api_key",
            "private_key",
            "authorization",
            "cookie",
            "set-cookie",
        ]

        def filter(self, record: logging.LogRecord) -> bool:
            if not hasattr(record, "msg"):
                return True

            msg = str(record.msg)
            for pattern in self.SENSITIVE_PATTERNS:
                msg = re.sub(
                    rf'("{pattern}"\s*[:=]\s*"[^"]{(3,)}")',
                    lambda m: m.group(1)[: len(pattern) + 4] + '***"',
                    msg,
                    flags=re.IGNORECASE,
                )
            record.msg = msg
            return True

    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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

    Yields:
        None

    Raises:
        Exception: 数据库初始化或技能发现失败时抛出。
    """
    settings = get_settings()
    logger.info("Starting DevMatrix application (debug=%s)", settings.debug)

    # 自动执行数据库迁移（如果 alembic 配置存在）
    try:
        from alembic.config import Config

        from alembic import command

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied")
    except Exception:
        logger.warning("Database migration skipped (alembic not configured)")

    try:
        init_db()
        logger.info("Database initialized")
    except Exception:
        logger.exception("Database initialization failed")
        raise
    try:
        from app.api.settings import init_default_configs
        from app.api.workflow_config import seed_templates
        from app.state.models import get_db

        db = next(get_db())
        try:
            seed_templates(db)
            init_default_configs(db)
        finally:
            db.close()
    except Exception:
        logger.exception("Template seeding failed")
        raise
    try:
        from app.core.registry.agent_registry import _register_builtin_agents

        _register_builtin_agents()
        logger.info("Built-in agents registered")
    except Exception:
        logger.exception("Agent registration failed")
        raise
    try:
        discover_and_register("app.skills", skill_registry, BaseSkill)
        logger.info("Skill discovery completed")
    except Exception:
        logger.exception("Skill discovery failed")
        raise
    try:
        from app.scheduler.engine import init_scheduler

        scheduler = init_scheduler()
        app.state.scheduler = scheduler
        logger.info("Task scheduler initialized")
    except Exception:
        logger.exception("Task scheduler initialization failed")
    yield
    if hasattr(app.state, "scheduler") and app.state.scheduler:
        app.state.scheduler.shutdown()
    logger.info("Shutting down DevMatrix application")


app = FastAPI(
    title="DevMatrix",
    description="Multi-role Collaborative Software Development Agent Operating System",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，返回标准化的错误响应。

    Args:
        request: 当前请求对象。
        exc: 捕获的异常实例。

    Returns:
        JSONResponse: 包含错误详情和请求 ID 的 JSON 响应。
    """
    request_id = getattr(request.state, "request_id", None)
    logger.exception(
        "Unhandled exception for request %s %s (request_id=%s)",
        request.method,
        request.url.path,
        request_id,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
        },
    )


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """HTTP 中间件，记录所有传入请求及其响应。

    为每个请求生成唯一请求 ID，记录请求开始、完成和失败信息，
    以及请求耗时。

    Args:
        request: 当前请求对象。
        call_next: 调用下一个中间件或路由处理器的函数。

    Returns:
        Response: HTTP 响应对象。

    Raises:
        Exception: 请求处理过程中抛出的异常。
    """
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    start_time = time.time()
    logger.info(
        "Request started: %s %s (request_id=%s)",
        request.method,
        request.url.path,
        request_id,
    )

    try:
        response = await call_next(request)
    except Exception as exc:
        duration = (time.time() - start_time) * 1000
        logger.error(
            "Request failed: %s %s (request_id=%s, duration=%.2fms, error=%s)",
            request.method,
            request.url.path,
            request_id,
            duration,
            exc,
        )
        raise

    duration = (time.time() - start_time) * 1000
    logger.info(
        "Request completed: %s %s (request_id=%s, status=%d, duration=%.2fms)",
        request.method,
        request.url.path,
        request_id,
        response.status_code,
        duration,
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 公开路由（无需认证）
app.include_router(auth_api.router, prefix="/api/auth", tags=["auth"])
app.include_router(menus_api.router, prefix="/api/menus", tags=["menus"])  # 登录前需要获取菜单

# 受保护路由（需要认证）
from app.api.deps import get_current_user

protected_routers = [
    (requirements.router, "/api/requirements", ["requirements"]),
    (approvals.router, "/api/approvals", ["approvals"]),
    (workflow.router, "/api/workflow", ["workflow"]),
    (registry.router, "/api/registry", ["registry"]),
    (workflow_config.router, "/api/workflow-config", ["workflow-config"]),
    (workbench.router, "/api/workbench", ["workbench"]),
    (events.router, "/api/events", ["events"]),
    (lifecycle.router, "/api/lifecycle", ["lifecycle"]),
    (workflow_instance.router, "/api/workflow-instances", ["workflow-instances"]),
    (projects.router, "/api/projects", ["projects"]),
    (settings_api.router, "/api/settings", ["settings"]),
    (scheduled_tasks.router, "/api/scheduled-tasks", ["scheduled-tasks"]),
    (task_management.router, "/api/tasks", ["tasks"]),
    (code_review.router, "/api/code-reviews", ["code-reviews"]),
    (users_api.router, "/api/users", ["users"]),
    (roles_api.router, "/api/roles", ["roles"]),
    (audit_api.router, "/api/audit", ["audit"]),
]

for router, prefix, tags in protected_routers:
    app.include_router(
        router,
        prefix=prefix,
        tags=tags,
        dependencies=[Depends(get_current_user)],
    )

# 注册健康检查路由（公开，无需认证）
app.include_router(health_api.router)

# 注册审计中间件（在请求日志中间件之后）
app.middleware("http")(audit_middleware)
