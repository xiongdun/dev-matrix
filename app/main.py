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

from fastapi import FastAPI, Request
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
)
from app.skills.registry import _global_registry as skill_registry
from app.skills.base import BaseSkill
from app.core.registry.discovery import discover_and_register


class ErrorResponse(BaseModel):
    """标准错误响应模型。

    Attributes:
        detail: 错误详情描述。
        request_id: 关联的请求 ID，用于追踪。
    """

    detail: str
    request_id: str | None = None


def configure_logging() -> None:
    """配置应用程序的结构化日志。

    根据 debug 设置日志级别，配置标准输出流处理器，
    并降低第三方库的日志噪音。

    Returns:
        None
    """
    settings = get_settings()
    log_level = logging.DEBUG if settings.debug else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

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
    try:
        init_db()
        logger.info("Database initialized")
    except Exception:
        logger.exception("Database initialization failed")
        raise
    try:
        from app.state.models import get_db
        from app.api.workflow_config import seed_templates
        from app.api.settings import init_default_configs

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
            "detail": f"Internal server error: {exc}",
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

app.include_router(requirements.router, prefix="/api/requirements", tags=["requirements"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["approvals"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])
app.include_router(registry.router, prefix="/api/registry", tags=["registry"])
app.include_router(
    workflow_config.router, prefix="/api/workflow-config", tags=["workflow-config"]
)
app.include_router(workbench.router, prefix="/api/workbench", tags=["workbench"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(lifecycle.router, prefix="/api/lifecycle", tags=["lifecycle"])
app.include_router(
    workflow_instance.router, prefix="/api/workflow-instances", tags=["workflow-instances"]
)
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])
app.include_router(scheduled_tasks.router, prefix="/api/scheduled-tasks", tags=["scheduled-tasks"])
app.include_router(task_management.router, prefix="/api/tasks", tags=["tasks"])


@app.get("/health")
async def health_check():
    """健康检查端点。

    Returns:
        dict: 包含状态 "ok" 的字典。
    """
    return {"status": "ok"}
