# 批次 1：安全加固实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 Critical 级别的安全问题，包括 JWT Secret 硬编码、API 无认证保护、无 API 限流、CORS 过宽。

**Architecture:** 通过密钥管理模块自动生成和持久化 JWT Secret；使用 FastAPI Depends 统一保护 API 路由；引入 slowapi 实现基于内存的限流；CORS 配置从环境变量读取允许的来源。

**Tech Stack:** Python 3.10+, FastAPI, slowapi, SQLAlchemy, PyJWT, bcrypt

---

## 文件变更总览

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/core/secrets.py` | 创建 | 密钥管理模块：自动生成、持久化、读取 JWT Secret |
| `app/core/security.py` | 修改 | 从 secrets 模块动态获取 SECRET_KEY |
| `app/state/models.py` | 修改 | 新增 SystemSecretModel 用于存储密钥 |
| `app/api/auth.py` | 修改 | 公开路由标记，提取 get_current_user 到 deps |
| `app/api/deps.py` | 修改 | 添加 get_current_user、require_permission 依赖 |
| `app/main.py` | 修改 | 注册限流中间件、收紧 CORS、改进错误处理 |
| `app/config.py` | 修改 | 添加 allowed_origins、rate_limit 配置 |
| `requirements.txt` | 修改 | 添加 slowapi 依赖 |
| `tests/test_security.py` | 创建 | 安全相关单元测试 |

---

## Task 1: 密钥管理模块 (app/core/secrets.py)

**Files:**
- Create: `app/core/secrets.py`
- Modify: `app/state/models.py`
- Test: `tests/test_secrets.py`

**背景:** 当前 `app/core/security.py` 中 `SECRET_KEY` 是硬编码的 fallback 值，存在严重安全隐患。

- [ ] **Step 1: 新增 SystemSecretModel 数据库模型**

在 `app/state/models.py` 中添加：

```python
class SystemSecretModel(Base):
    """系统密钥存储模型。

    用于安全地存储 JWT Secret 等系统级密钥。
    """
    __tablename__ = "system_secrets"

    id = Column(Integer, primary_key=True)
    key_name = Column(String(64), unique=True, nullable=False, index=True)
    key_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: 创建密钥管理模块**

创建 `app/core/secrets.py`：

```python
"""系统密钥管理模块。

提供 JWT Secret 等系统级密钥的自动生成、安全存储和读取功能。
首次启动时自动生成 256 位随机密钥并持久化到数据库，后续复用。
"""

import secrets
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.state.models import SystemSecretModel

logger = logging.getLogger(__name__)

DEFAULT_SECRET_KEY_NAME = "jwt_secret_key"
SECRET_KEY_LENGTH = 64  # 512 bits


def generate_secret_key(length: int = SECRET_KEY_LENGTH) -> str:
    """生成加密安全的随机密钥。

    Args:
        length: 密钥字符长度，默认 64（512 bits）。

    Returns:
        str: 十六进制编码的随机密钥。
    """
    return secrets.token_hex(length // 2)


def get_or_create_secret(db: Session, key_name: str = DEFAULT_SECRET_KEY_NAME) -> str:
    """获取或创建系统密钥。

    如果数据库中已存在该密钥，直接返回；否则生成新密钥并保存。

    Args:
        db: 数据库会话。
        key_name: 密钥名称。

    Returns:
        str: 密钥值。
    """
    secret = db.query(SystemSecretModel).filter(SystemSecretModel.key_name == key_name).first()
    if secret:
        return secret.key_value

    # 生成新密钥
    new_key = generate_secret_key()
    secret = SystemSecretModel(key_name=key_name, key_value=new_key)
    db.add(secret)
    db.commit()
    logger.info("Generated new system secret: %s", key_name)
    return new_key


def get_secret(db: Session, key_name: str = DEFAULT_SECRET_KEY_NAME) -> Optional[str]:
    """获取系统密钥。

    Args:
        db: 数据库会话。
        key_name: 密钥名称。

    Returns:
        Optional[str]: 密钥值，不存在则返回 None。
    """
    secret = db.query(SystemSecretModel).filter(SystemSecretModel.key_name == key_name).first()
    return secret.key_value if secret else None


def rotate_secret(db: Session, key_name: str = DEFAULT_SECRET_KEY_NAME) -> str:
    """轮换系统密钥。

    生成新密钥并更新数据库。注意：轮换后所有已颁发的 Token 将失效。

    Args:
        db: 数据库会话。
        key_name: 密钥名称。

    Returns:
        str: 新密钥值。
    """
    new_key = generate_secret_key()
    secret = db.query(SystemSecretModel).filter(SystemSecretModel.key_name == key_name).first()
    if secret:
        secret.key_value = new_key
    else:
        secret = SystemSecretModel(key_name=key_name, key_value=new_key)
        db.add(secret)
    db.commit()
    logger.warning("Rotated system secret: %s. All existing tokens are now invalid.", key_name)
    return new_key
```

- [ ] **Step 3: 修改 security.py 使用动态密钥**

修改 `app/core/security.py`：

```python
"""安全工具模块。

提供密码哈希、JWT Token 生成/验证等安全相关功能。
"""

import bcrypt
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.core.secrets import get_or_create_secret

logger = logging.getLogger(__name__)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 延迟获取 SECRET_KEY，避免在导入时查询数据库
_SECRET_KEY: Optional[str] = None


def get_secret_key(db: Session) -> str:
    """获取 JWT Secret Key（从数据库或自动生成）。"""
    global _SECRET_KEY
    if _SECRET_KEY is None:
        _SECRET_KEY = get_or_create_secret(db)
    return _SECRET_KEY


def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码。"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码。"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(db: Session, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Access Token。"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    secret = get_secret_key(db)
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def create_refresh_token(db: Session, data: Dict) -> str:
    """创建 JWT Refresh Token。"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    secret = get_secret_key(db)
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def decode_token(db: Session, token: str) -> Optional[Dict]:
    """解码并验证 JWT Token。"""
    try:
        secret = get_secret_key(db)
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

- [ ] **Step 4: 更新 auth.py 适配新的 security 签名**

修改 `app/api/auth.py` 中所有调用 `create_access_token`、`create_refresh_token`、`decode_token` 的地方，传入 `db` 参数。

- [ ] **Step 5: 运行测试**

```bash
cd /Users/Summer/Documents/works/codes/dev-matrix
python -m pytest tests/test_secrets.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/core/secrets.py app/core/security.py app/state/models.py app/api/auth.py tests/test_secrets.py
git commit -m "security: add auto-generated JWT secret key management"
```

---

## Task 2: API 统一认证保护

**Files:**
- Modify: `app/api/deps.py`
- Modify: `app/api/auth.py`
- Modify: `app/main.py`
- Test: `tests/test_auth_protection.py`

**背景:** 当前只有 `/auth/*` 等少数路由有认证，大部分 API 路由未受保护。

- [ ] **Step 1: 完善 deps.py 添加认证依赖**

修改 `app/api/deps.py`：

```python
"""API 依赖模块。

提供 FastAPI 路由使用的依赖注入函数。
"""

from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.state.models import get_db, UserModel
from app.core.security import decode_token

__all__ = ["get_db", "get_current_user", "require_permission"]


def get_current_user(request: Request, db: Session = Depends(get_db)) -> UserModel:
    """从请求头获取当前已认证用户。

    Args:
        request: FastAPI 请求对象。
        db: 数据库会话。

    Returns:
        UserModel: 当前用户模型。

    Raises:
        HTTPException: 401 如果 Token 缺失、无效或过期。
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = auth_header[7:]
    payload = decode_token(db, token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(UserModel).filter(UserModel.id == payload.get("sub")).first()
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="User not found or disabled")

    return user


def require_permission(permission: str):
    """创建依赖项，要求用户具有指定权限。

    Args:
        permission: 所需权限标识。

    Returns:
        Callable: FastAPI 依赖函数。
    """
    def checker(user: UserModel = Depends(get_current_user)) -> UserModel:
        # 权限检查逻辑：从用户角色关联的菜单中获取权限列表
        from app.state.models import UserRoleModel, RoleMenuModel, MenuModel
        from sqlalchemy.orm import Session
        from fastapi import Depends
        from app.api.deps import get_db

        db: Session = Depends(get_db)
        role_ids = db.query(UserRoleModel.role_id).filter(UserRoleModel.user_id == user.id).all()
        role_ids = [r[0] for r in role_ids]
        if not role_ids:
            raise HTTPException(status_code=403, detail="Permission denied")

        menu_ids = db.query(RoleMenuModel.menu_id).filter(RoleMenuModel.role_id.in_(role_ids)).all()
        menu_ids = [m[0] for m in menu_ids]

        permissions = db.query(MenuModel.permission).filter(
            MenuModel.id.in_(menu_ids),
            MenuModel.permission.isnot(None)
        ).all()
        user_permissions = [p[0] for p in permissions]

        if permission not in user_permissions:
            raise HTTPException(status_code=403, detail=f"Permission '{permission}' required")
        return user
    return checker
```

- [ ] **Step 2: 为所有非公开 API 路由添加认证保护**

修改 `app/main.py`，将路由分为公开和受保护两组：

```python
# 公开路由（无需认证）
app.include_router(auth_api.router, prefix="/api/auth", tags=["auth"])
app.include_router(menus_api.router, prefix="/api/menus", tags=["menus"])  # 登录前需要获取菜单

# 受保护路由（需要认证）
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
]

for router, prefix, tags in protected_routers:
    # 为受保护路由添加全局认证依赖
    from app.api.deps import get_current_user
    app.include_router(
        router,
        prefix=prefix,
        tags=tags,
        dependencies=[Depends(get_current_user)],
    )
```

- [ ] **Step 3: 运行测试**

```bash
python -m pytest tests/test_auth_protection.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add app/api/deps.py app/main.py tests/test_auth_protection.py
git commit -m "security: add unified API authentication protection"
```

---

## Task 3: API 限流 (Rate Limiting)

**Files:**
- Modify: `requirements.txt`
- Modify: `app/main.py`
- Modify: `app/config.py`
- Test: `tests/test_rate_limit.py`

**背景:** 当前无 API 限流，易受暴力破解和 DDoS 攻击。

- [ ] **Step 1: 添加 slowapi 依赖**

修改 `requirements.txt`，添加：

```
slowapi==0.1.9
```

- [ ] **Step 2: 修改配置添加限流配置**

修改 `app/config.py`：

```python
class Settings(BaseSettings):
    # ... 现有配置 ...

    # 限流配置
    rate_limit_login: str = "5/minute"
    rate_limit_default: str = "100/minute"
    rate_limit_enabled: bool = True
```

- [ ] **Step 3: 在 main.py 中注册限流中间件**

修改 `app/main.py`：

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 创建限流器
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="DevMatrix",
    description="Multi-role Collaborative Software Development Agent Operating System",
    version="0.1.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 为登录路由添加限流
@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login_with_rate_limit(request: Request, ...):
    ...
```

或者使用装饰器方式在 auth.py 中：

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.main import limiter

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    ...
```

- [ ] **Step 4: 运行测试**

```bash
pip install slowapi
python -m pytest tests/test_rate_limit.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add requirements.txt app/config.py app/main.py app/api/auth.py tests/test_rate_limit.py
git commit -m "security: add API rate limiting with slowapi"
```

---

## Task 4: CORS 配置收紧

**Files:**
- Modify: `app/config.py`
- Modify: `app/main.py`

**背景:** 当前 CORS 允许所有来源 (`["*"]`)，生产环境存在安全风险。

- [ ] **Step 1: 修改配置添加 allowed_origins**

修改 `app/config.py`：

```python
class Settings(BaseSettings):
    # ... 现有配置 ...

    # CORS 配置
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    def get_allowed_origins(self) -> list:
        """解析允许的来源列表。"""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
```

- [ ] **Step 2: 修改 main.py 使用配置的 CORS**

修改 `app/main.py`：

```python
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
```

- [ ] **Step 3: 运行测试**

```bash
python -m pytest tests/test_cors.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add app/config.py app/main.py tests/test_cors.py
git commit -m "security: tighten CORS configuration from environment"
```

---

## Task 5: 改进全局错误处理

**Files:**
- Modify: `app/main.py`

**背景:** 当前全局异常处理器返回 `Internal server error: {exc}`，可能泄露内部信息。

- [ ] **Step 1: 改进全局异常处理**

修改 `app/main.py`：

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，返回标准化的错误响应。

    生产环境不暴露内部错误详情，只记录到日志。
    """
    request_id = getattr(request.state, "request_id", None)
    logger.exception(
        "Unhandled exception for request %s %s (request_id=%s)",
        request.method,
        request.url.path,
        request_id,
    )

    settings = get_settings()
    if settings.debug:
        # 调试模式返回详细错误
        detail = f"Internal server error: {exc}"
    else:
        # 生产环境返回通用错误
        detail = "Internal server error"

    return JSONResponse(
        status_code=500,
        content={
            "detail": detail,
            "request_id": request_id,
        },
    )
```

- [ ] **Step 2: Commit**

```bash
git add app/main.py
git commit -m "security: improve global error handler to avoid info leak"
```

---

## 批次 1 验收检查

- [ ] JWT Secret 从数据库读取，不再使用硬编码
- [ ] 未登录访问 `/api/requirements` 等受保护路由返回 401
- [ ] 登录接口 5 次/分钟限流生效
- [ ] CORS 只允许配置的来源
- [ ] 生产环境 500 错误不暴露内部异常信息
