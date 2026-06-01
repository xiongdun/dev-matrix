# 批次 2：基础设施实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 引入 Alembic 数据库迁移、加固 Docker 安全、扩展健康检查端点。

**Architecture:** Alembic 管理数据库 schema 变更；Docker 多阶段构建 + 非 root 用户；健康检查端点扩展为 /health/ready（依赖检查）和 /health/live（存活检查）。

**Tech Stack:** Python 3.10+, Alembic, Docker, docker-compose, FastAPI

---

## 文件变更总览

| 文件 | 操作 | 说明 |
|------|------|------|
| `alembic.ini` | 创建 | Alembic 配置文件 |
| `alembic/env.py` | 创建 | Alembic 环境脚本 |
| `alembic/versions/` | 创建 | 迁移脚本目录 |
| `app/api/health.py` | 创建 | 健康检查路由模块 |
| `app/main.py` | 修改 | 注册健康检查路由 |
| `Dockerfile` | 修改 | 多阶段构建 + 非 root 用户 |
| `.dockerignore` | 创建 | Docker 构建忽略文件 |
| `docker-compose.yml` | 修改 | 添加 healthcheck、restart 策略 |
| `requirements.txt` | 修改 | 添加 alembic 依赖 |
| `tests/test_health.py` | 创建 | 健康检查测试 |

---

## Task 1: Alembic 数据库迁移

**Files:**
- Create: `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`
- Create: `alembic/versions/20260526_initial.py`
- Modify: `requirements.txt`
- Modify: `app/main.py`
- Test: `tests/test_alembic.py`

**背景:** 当前无数据库迁移工具，模型变更需要手动删库重建。

- [ ] **Step 1: 添加 alembic 依赖**

修改 `requirements.txt`，添加：

```
alembic==1.13.1
```

- [ ] **Step 2: 初始化 Alembic 配置**

创建 `alembic.ini`：

```ini
# Alembic 配置文件
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 3: 创建 Alembic 环境脚本**

创建 `alembic/env.py`：

```python
"""Alembic 环境配置脚本。

提供迁移运行时所需的数据库连接和元数据。
"""

import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# 将项目根目录加入路径
sys.path.append(".")

from app.config import get_settings
from app.state.models import Base

settings = get_settings()
config = context.config

# 从应用配置设置数据库 URL
config.set_main_option("sqlalchemy.url", settings.database_url)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据
 target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移（生成 SQL 脚本）。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移（直接操作数据库）。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: 创建迁移脚本模板**

创建 `alembic/script.py.mako`：

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 5: 创建初始迁移脚本**

创建 `alembic/versions/20260526_initial.py`：

```python
"""Initial migration

Revision ID: 20260526_initial
Revises:
Create Date: 2026-05-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260526_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建所有表（基于当前模型）
    # Alembic 会自动检测，这里留空让 autogenerate 生成
    pass


def downgrade() -> None:
    pass
```

- [ ] **Step 6: 在应用启动时自动执行迁移**

修改 `app/main.py` 的 `lifespan`：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting DevMatrix application (debug=%s)", settings.debug)

    # 自动执行数据库迁移
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied")
    except Exception:
        logger.exception("Database migration failed")
        raise

    try:
        init_db()
        logger.info("Database initialized")
    except Exception:
        logger.exception("Database initialization failed")
        raise

    # ... 其余启动逻辑保持不变 ...
    yield
    # ... 关闭逻辑 ...
```

- [ ] **Step 7: 运行测试**

```bash
cd /Users/Summer/Documents/works/codes/dev-matrix
pip install alembic
alembic revision --autogenerate -m "initial"
alembic upgrade head
python -m pytest tests/test_alembic.py -v
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add alembic.ini alembic/ requirements.txt app/main.py tests/test_alembic.py
git commit -m "infra: add Alembic database migration support"
```

---

## Task 2: Docker 安全加固

**Files:**
- Modify: `Dockerfile`
- Create: `.dockerignore`
- Test: `tests/test_docker.py`

**背景:** 当前 Dockerfile 以 root 用户运行，且没有多阶段构建。

- [ ] **Step 1: 重写 Dockerfile**

修改 `Dockerfile`：

```dockerfile
# 构建阶段
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖并安装到虚拟环境
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.11-slim

# 创建非 root 用户
RUN groupadd -r devmatrix && useradd -r -g devmatrix devmatrix

WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY app/ ./app/
COPY config/ ./config/
COPY alembic.ini .
COPY alembic/ ./alembic/

# 创建日志目录并设置权限
RUN mkdir -p logs && chown -R devmatrix:devmatrix /app

# 切换到非 root 用户
USER devmatrix

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')" || exit 1

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: 创建 .dockerignore**

创建 `.dockerignore`：

```
# Git
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build

# 虚拟环境
venv/
env/
ENV/

# IDE
.idea
.vscode
*.swp
*.swo

# 测试
tests/
.pytest_cache
.coverage

# 文档
docs/
*.md

# 前端（单独构建）
frontend/
node_modules/

# 本地数据
*.db
*.sqlite
*.sqlite3
logs/

# Docker
Dockerfile
docker-compose.yml
.dockerignore
```

- [ ] **Step 3: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "infra: harden Docker with multi-stage build and non-root user"
```

---

## Task 3: 健康检查扩展

**Files:**
- Create: `app/api/health.py`
- Modify: `app/main.py`
- Modify: `docker-compose.yml`
- Test: `tests/test_health.py`

**背景:** 当前只有简单的 `/health` 返回 `{"status": "ok"}`，无法检测依赖服务状态。

- [ ] **Step 1: 创建健康检查路由模块**

创建 `app/api/health.py`：

```python
"""健康检查 API 模块。

提供应用和依赖服务的健康状态检查端点。
- /health/live — 存活探针（应用是否运行）
- /health/ready — 就绪探针（依赖服务是否可用）
- /health — 综合健康状态
"""

import logging
from typing import Dict, List

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
    checks: Dict[str, str]


class HealthResponse(BaseModel):
    """健康检查响应模型。"""
    status: str
    version: str = "0.1.0"
    checks: Dict[str, Dict[str, str]]


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
    checks["temporal"] = {"status": "healthy" if temporal_ok else "unhealthy", "detail": temporal_status}

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
```

- [ ] **Step 2: 修改 main.py 注册健康检查路由**

修改 `app/main.py`，移除旧的 `/health` 端点，注册新的 health 路由：

```python
from app.api import (
    # ... 现有导入 ...
    health as health_api,
)

# 移除旧的 @app.get("/health") 端点

# 注册健康检查路由（公开，无需认证）
app.include_router(health_api.router, tags=["health"])
```

- [ ] **Step 3: 更新 docker-compose 添加健康检查**

修改 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: devmatrix-app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://devmatrix:devmatrix@postgres:5432/devmatrix
      - REDIS_URL=redis://redis:6379/0
      - TEMPORAL_HOST=temporal-server:7233
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      temporal-server:
        condition: service_started
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  temporal-server:
    image: temporalio/auto-setup:latest
    container_name: devmatrix-temporal
    ports:
      - "7233:7233"
      - "8088:8088"
    environment:
      - DB=sqlite
      - SQLITE_PRAGMAS=journal_mode=WAL
      - TEMPORAL_CLI_ADDRESS=temporal-server:7233
    volumes:
      - temporal-data:/tmp/temporal
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8088/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: devmatrix-postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=devmatrix
      - POSTGRES_PASSWORD=devmatrix
      - POSTGRES_DB=devmatrix
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U devmatrix -d devmatrix"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: devmatrix-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    restart: unless-stopped

volumes:
  temporal-data:
  postgres-data:
  redis-data:
```

- [ ] **Step 4: 运行测试**

```bash
python -m pytest tests/test_health.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/health.py app/main.py docker-compose.yml tests/test_health.py
git commit -m "infra: extend health checks with liveness and readiness probes"
```

---

## 批次 2 验收检查

- [ ] `alembic revision --autogenerate` 能成功生成迁移脚本
- [ ] `alembic upgrade head` 能成功应用迁移
- [ ] Docker 镜像以非 root 用户运行
- [ ] Docker 镜像体积减小（多阶段构建）
- [ ] `/health/live` 返回 `{"status": "healthy"}`
- [ ] `/health/ready` 检查数据库、Temporal、Redis 状态
- [ ] docker-compose 服务有健康检查和自动重启策略
