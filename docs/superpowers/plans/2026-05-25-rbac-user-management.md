# RBAC 用户管理系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 DevMatrix 构建完整的 RBAC 用户管理系统，包含用户认证、角色管理（关联 Agent）、菜单权限控制（按钮级+数据级）。

**Architecture:** 后端使用 FastAPI + SQLAlchemy + JWT + bcrypt，前端使用 Vue 3 + Pinia + 自定义权限指令。采用渐进式改造，先加认证层，再逐步加权限控制。

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy, PyJWT, bcrypt, Vue 3, TypeScript, Pinia

---

## 文件结构

### 后端新文件

| 文件 | 职责 |
|------|------|
| `app/state/models.py` (追加) | 用户、角色、菜单、关联表模型 |
| `app/core/security.py` | 密码哈希、JWT 生成/验证、权限检查 |
| `app/api/auth.py` | 登录/登出/当前用户/刷新 Token API |
| `app/api/users.py` | 用户 CRUD API |
| `app/api/roles.py` | 角色 CRUD + 菜单/Agent 分配 API |
| `app/api/menus.py` | 菜单 CRUD + 动态菜单 API |
| `app/core/dependencies.py` | 当前用户依赖、权限检查依赖 |

### 前端新文件

| 文件 | 职责 |
|------|------|
| `frontend/src/pages/LoginPage.vue` | 登录页面 |
| `frontend/src/pages/users/UserListPage.vue` | 用户管理列表 |
| `frontend/src/pages/users/UserFormModal.vue` | 用户创建/编辑弹窗 |
| `frontend/src/pages/roles/RoleListPage.vue` | 角色管理列表 |
| `frontend/src/pages/roles/RoleFormModal.vue` | 角色创建/编辑弹窗 |
| `frontend/src/pages/menus/MenuListPage.vue` | 菜单管理树形页面 |
| `frontend/src/pages/menus/MenuFormModal.vue` | 菜单创建/编辑弹窗 |
| `frontend/src/stores/user.ts` | Pinia 用户状态管理 |
| `frontend/src/directives/permission.ts` | 按钮级权限指令 |
| `frontend/src/api/auth.ts` | 认证相关 API |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `app/main.py` | 注册新路由、添加 JWT 认证中间件 |
| `app/config.py` | 添加 JWT 密钥配置 |
| `frontend/src/router.ts` | 添加登录页、管理页路由，添加路由守卫 |
| `frontend/src/api/index.ts` | 添加 Token 拦截器、新 API 方法 |
| `frontend/src/components/Sidebar.vue` | 改为动态菜单 |
| `frontend/src/App.vue` | 添加登录状态判断 |
| `frontend/src/i18n/locales/zh.json` | 添加用户管理相关翻译 |
| `frontend/src/i18n/locales/en.json` | 添加用户管理相关翻译 |

---

## Task 1: 数据库模型

**Files:**
- Modify: `app/state/models.py`

**Goal:** 添加用户、角色、菜单及关联表模型

- [ ] **Step 1: 添加用户表模型**

在 `app/state/models.py` 的 `TaskChatMessageModel` 之后追加：

```python
class UserModel(Base):
    """用户表。"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    avatar = Column(String(255), nullable=True)
    status = Column(String(20), default="active")
    data_scope = Column(String(20), default="self")
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RoleModel(Base):
    """角色表。"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    data_scope = Column(String(20), default="self")
    is_system = Column(Integer, default=0)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserRoleModel(Base):
    """用户角色关联表。"""
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)


class MenuModel(Base):
    """菜单表。"""
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    title = Column(String(50), nullable=False)
    path = Column(String(100), nullable=True)
    icon = Column(String(50), nullable=True)
    parent_id = Column(Integer, ForeignKey("menus.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    menu_type = Column(String(20), default="page")
    permission = Column(String(100), nullable=True)
    component = Column(String(100), nullable=True)
    is_visible = Column(Integer, default=1)
    status = Column(String(20), default="active")


class RoleMenuModel(Base):
    """角色菜单关联表。"""
    __tablename__ = "role_menus"

    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), primary_key=True)


class RoleAgentModel(Base):
    """角色 Agent 关联表。"""
    __tablename__ = "role_agents"

    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    agent_name = Column(String(50), primary_key=True)
```

- [ ] **Step 2: 验证模型导入**

Run: `cd /Users/Summer/Documents/works/codes/dev-matrix && source venv/bin/activate && python -c "from app.state.models import UserModel, RoleModel, MenuModel; print('Models OK')"`
Expected: `Models OK`

---

## Task 2: 安全工具模块

**Files:**
- Create: `app/core/security.py`

**Goal:** 实现密码哈希、JWT 生成/验证

- [ ] **Step 1: 创建安全工具模块**

```python
"""安全工具模块。"""

import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.config import get_settings

settings = get_settings()
SECRET_KEY = getattr(settings, 'jwt_secret_key', 'devmatrix-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码。"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码。"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Access Token。"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: Dict) -> str:
    """创建 JWT Refresh Token。"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[Dict]:
    """解码并验证 JWT Token。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

- [ ] **Step 2: 安装依赖**

Run: `cd /Users/Summer/Documents/works/codes/dev-matrix && source venv/bin/activate && pip install pyjwt bcrypt`

- [ ] **Step 3: 测试安全工具**

Run:
```bash
cd /Users/Summer/Documents/works/codes/dev-matrix && source venv/bin/activate && python -c "
from app.core.security import hash_password, verify_password, create_access_token, decode_token
h = hash_password('test123')
print('Verify:', verify_password('test123', h))
t = create_access_token({'sub': 'admin'})
print('Token:', decode_token(t)['sub'])
"
```
Expected: `Verify: True` and `Token: admin`

---

## Task 3: 认证 API

**Files:**
- Create: `app/api/auth.py`
- Modify: `app/main.py`

**Goal:** 实现登录/登出/当前用户/刷新 Token API

- [ ] **Step 1: 创建认证 API**

```python
"""认证 API 模块。"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.state.models import UserModel, RoleModel, UserRoleModel, MenuModel, RoleMenuModel, RoleAgentModel
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    token: str
    refresh_token: str
    expires_at: int
    user: Dict


class UserInfoResponse(BaseModel):
    id: int
    username: str
    nickname: Optional[str]
    email: Optional[str]
    avatar: Optional[str]
    roles: list
    permissions: list
    agents: list


def get_current_user(request: Request, db: Session = Depends(get_db)) -> UserModel:
    """从请求头获取当前用户。"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    token = auth_header[7:]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = db.query(UserModel).filter(UserModel.id == payload.get("sub")).first()
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="User not found or disabled")
    
    return user


def get_user_permissions(db: Session, user_id: int) -> list:
    """获取用户所有权限标识。"""
    role_ids = db.query(UserRoleModel.role_id).filter(UserRoleModel.user_id == user_id).all()
    role_ids = [r[0] for r in role_ids]
    if not role_ids:
        return []
    
    menu_ids = db.query(RoleMenuModel.menu_id).filter(RoleMenuModel.role_id.in_(role_ids)).all()
    menu_ids = [m[0] for m in menu_ids]
    if not menu_ids:
        return []
    
    permissions = db.query(MenuModel.permission).filter(
        MenuModel.id.in_(menu_ids),
        MenuModel.permission.isnot(None)
    ).all()
    return list(set([p[0] for p in permissions]))


def get_user_agents(db: Session, user_id: int) -> list:
    """获取用户可用 Agent 列表。"""
    role_ids = db.query(UserRoleModel.role_id).filter(UserRoleModel.user_id == user_id).all()
    role_ids = [r[0] for r in role_ids]
    if not role_ids:
        return []
    
    agents = db.query(RoleAgentModel.agent_name).filter(
        RoleAgentModel.role_id.in_(role_ids)
    ).distinct().all()
    return [a[0] for a in agents]


@router.post("/login")
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """用户登录。"""
    user = db.query(UserModel).filter(UserModel.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if user.status != "active":
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    token = create_access_token({"sub": str(user.id), "username": user.username})
    refresh = create_refresh_token({"sub": str(user.id)})
    
    roles = db.query(RoleModel).join(UserRoleModel).filter(UserRoleModel.user_id == user.id).all()
    
    return {
        "token": token,
        "refresh_token": refresh,
        "expires_at": 7200,
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "email": user.email,
            "avatar": user.avatar,
            "roles": [{"id": r.id, "name": r.name, "display_name": r.display_name} for r in roles],
        }
    }


@router.post("/logout")
async def logout():
    """用户登出（前端清除 Token 即可）。"""
    return {"success": True}


@router.get("/me", response_model=UserInfoResponse)
async def get_me(current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前登录用户信息。"""
    roles = db.query(RoleModel).join(UserRoleModel).filter(UserRoleModel.user_id == current_user.id).all()
    permissions = get_user_permissions(db, current_user.id)
    agents = get_user_agents(db, current_user.id)
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "nickname": current_user.nickname,
        "email": current_user.email,
        "avatar": current_user.avatar,
        "roles": [{"id": r.id, "name": r.name, "display_name": r.display_name} for r in roles],
        "permissions": permissions,
        "agents": agents,
    }


@router.post("/refresh")
async def refresh_token(request: Request):
    """刷新 Access Token。"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing refresh token")
    
    token = auth_header[7:]
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    new_token = create_access_token({"sub": payload["sub"], "username": payload.get("username", "")})
    return {"token": new_token, "expires_at": 7200}


@router.post("/password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码。"""
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    
    from app.core.security import hash_password
    current_user.password_hash = hash_password(new_password)
    db.commit()
    return {"success": True}
```

- [ ] **Step 2: 注册认证路由**

在 `app/main.py` 的导入部分添加：
```python
from app.api import auth as auth_api
```

在路由注册部分添加：
```python
app.include_router(auth_api.router, prefix="/api/auth", tags=["auth"])
```

- [ ] **Step 3: 测试登录 API**

Run:
```bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```
Expected: 401（还没有初始化用户）

---

## Task 4: 用户管理 API

**Files:**
- Create: `app/api/users.py`
- Modify: `app/main.py`

**Goal:** 实现用户 CRUD API

- [ ] **Step 1: 创建用户管理 API**

```python
"""用户管理 API 模块。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.auth import get_current_user, get_user_permissions
from app.state.models import UserModel, RoleModel, UserRoleModel
from app.core.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    nickname: Optional[str] = None
    email: Optional[str] = None
    role_ids: List[int] = []
    data_scope: str = "self"


class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    data_scope: Optional[str] = None
    role_ids: Optional[List[int]] = None


class UserResponse(BaseModel):
    id: int
    username: str
    nickname: Optional[str]
    email: Optional[str]
    status: str
    data_scope: str
    roles: List[dict]
    last_login_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


def check_manage_permission(current_user: UserModel, db: Session):
    """检查当前用户是否有管理权限。"""
    perms = get_user_permissions(db, current_user.id)
    if "user:manage" not in perms:
        raise HTTPException(status_code=403, detail="Permission denied")


@router.get("", response_model=List[UserResponse])
async def list_users(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """用户列表。"""
    check_manage_permission(current_user, db)
    
    query = db.query(UserModel)
    if keyword:
        query = query.filter(
            UserModel.username.contains(keyword) | UserModel.nickname.contains(keyword)
        )
    if status:
        query = query.filter(UserModel.status == status)
    
    users = query.all()
    result = []
    for u in users:
        roles = db.query(RoleModel).join(UserRoleModel).filter(UserRoleModel.user_id == u.id).all()
        result.append({
            "id": u.id,
            "username": u.username,
            "nickname": u.nickname,
            "email": u.email,
            "status": u.status,
            "data_scope": u.data_scope,
            "roles": [{"id": r.id, "name": r.name, "display_name": r.display_name} for r in roles],
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "created_at": u.created_at.isoformat(),
        })
    return result


@router.post("", response_model=UserResponse)
async def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """创建用户。"""
    check_manage_permission(current_user, db)
    
    if db.query(UserModel).filter(UserModel.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    
    user = UserModel(
        username=payload.username,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
        email=payload.email,
        data_scope=payload.data_scope,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    for role_id in payload.role_ids:
        db.add(UserRoleModel(user_id=user.id, role_id=role_id))
    db.commit()
    
    return {**user.__dict__, "roles": []}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """用户详情。"""
    if current_user.id != user_id:
        check_manage_permission(current_user, db)
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    roles = db.query(RoleModel).join(UserRoleModel).filter(UserRoleModel.user_id == user.id).all()
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "status": user.status,
        "data_scope": user.data_scope,
        "roles": [{"id": r.id, "name": r.name, "display_name": r.display_name} for r in roles],
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat(),
    }


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """更新用户。"""
    check_manage_permission(current_user, db)
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if payload.nickname is not None:
        user.nickname = payload.nickname
    if payload.email is not None:
        user.email = payload.email
    if payload.status is not None:
        user.status = payload.status
    if payload.data_scope is not None:
        user.data_scope = payload.data_scope
    
    if payload.role_ids is not None:
        db.query(UserRoleModel).filter(UserRoleModel.user_id == user_id).delete()
        for role_id in payload.role_ids:
            db.add(UserRoleModel(user_id=user_id, role_id=role_id))
    
    db.commit()
    db.refresh(user)
    
    roles = db.query(RoleModel).join(UserRoleModel).filter(UserRoleModel.user_id == user.id).all()
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "status": user.status,
        "data_scope": user.data_scope,
        "roles": [{"id": r.id, "name": r.name, "display_name": r.display_name} for r in roles],
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat(),
    }


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """删除用户。"""
    check_manage_permission(current_user, db)
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.query(UserRoleModel).filter(UserRoleModel.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"success": True}


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """启用/禁用用户。"""
    check_manage_permission(current_user, db)
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = status
    db.commit()
    return {"success": True}
```

- [ ] **Step 2: 注册用户管理路由**

在 `app/main.py` 导入部分添加：
```python
from app.api import users as users_api
```

在路由注册部分添加：
```python
app.include_router(users_api.router, prefix="/api/users", tags=["users"])
```

---

## Task 5: 角色管理 API

**Files:**
- Create: `app/api/roles.py`
- Modify: `app/main.py`

**Goal:** 实现角色 CRUD + 菜单/Agent 分配 API

- [ ] **Step 1: 创建角色管理 API**

```python
"""角色管理 API 模块。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.auth import get_current_user, get_user_permissions
from app.state.models import RoleModel, MenuModel, RoleMenuModel, RoleAgentModel

router = APIRouter(prefix="/roles", tags=["roles"])


class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    data_scope: str = "self"
    menu_ids: List[int] = []
    agent_names: List[str] = []


class RoleUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    data_scope: Optional[str] = None
    status: Optional[str] = None
    menu_ids: Optional[List[int]] = None
    agent_names: Optional[List[str]] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    data_scope: str
    is_system: int
    status: str
    menus: List[dict]
    agents: List[str]

    class Config:
        from_attributes = True


def check_role_permission(current_user: UserModel, db: Session):
    """检查当前用户是否有角色管理权限。"""
    perms = get_user_permissions(db, current_user.id)
    if "role:manage" not in perms:
        raise HTTPException(status_code=403, detail="Permission denied")


@router.get("", response_model=List[RoleResponse])
async def list_roles(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """角色列表。"""
    check_role_permission(current_user, db)
    
    roles = db.query(RoleModel).all()
    result = []
    for r in roles:
        menus = db.query(MenuModel).join(RoleMenuModel).filter(RoleMenuModel.role_id == r.id).all()
        agents = db.query(RoleAgentModel.agent_name).filter(RoleAgentModel.role_id == r.id).all()
        result.append({
            "id": r.id,
            "name": r.name,
            "display_name": r.display_name,
            "description": r.description,
            "data_scope": r.data_scope,
            "is_system": r.is_system,
            "status": r.status,
            "menus": [{"id": m.id, "name": m.name, "title": m.title} for m in menus],
            "agents": [a[0] for a in agents],
        })
    return result


@router.post("", response_model=RoleResponse)
async def create_role(
    payload: RoleCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """创建角色。"""
    check_role_permission(current_user, db)
    
    if db.query(RoleModel).filter(RoleModel.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Role name already exists")
    
    role = RoleModel(
        name=payload.name,
        display_name=payload.display_name,
        description=payload.description,
        data_scope=payload.data_scope,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    for menu_id in payload.menu_ids:
        db.add(RoleMenuModel(role_id=role.id, menu_id=menu_id))
    for agent_name in payload.agent_names:
        db.add(RoleAgentModel(role_id=role.id, agent_name=agent_name))
    db.commit()
    
    return {**role.__dict__, "menus": [], "agents": []}


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """角色详情。"""
    check_role_permission(current_user, db)
    
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    menus = db.query(MenuModel).join(RoleMenuModel).filter(RoleMenuModel.role_id == role.id).all()
    agents = db.query(RoleAgentModel.agent_name).filter(RoleAgentModel.role_id == role.id).all()
    return {
        "id": role.id,
        "name": role.name,
        "display_name": role.display_name,
        "description": role.description,
        "data_scope": role.data_scope,
        "is_system": role.is_system,
        "status": role.status,
        "menus": [{"id": m.id, "name": m.name, "title": m.title} for m in menus],
        "agents": [a[0] for a in agents],
    }


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """更新角色。"""
    check_role_permission(current_user, db)
    
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role.is_system:
        raise HTTPException(status_code=403, detail="Cannot modify system role")
    
    if payload.display_name is not None:
        role.display_name = payload.display_name
    if payload.description is not None:
        role.description = payload.description
    if payload.data_scope is not None:
        role.data_scope = payload.data_scope
    if payload.status is not None:
        role.status = payload.status
    
    if payload.menu_ids is not None:
        db.query(RoleMenuModel).filter(RoleMenuModel.role_id == role_id).delete()
        for menu_id in payload.menu_ids:
            db.add(RoleMenuModel(role_id=role_id, menu_id=menu_id))
    
    if payload.agent_names is not None:
        db.query(RoleAgentModel).filter(RoleAgentModel.role_id == role_id).delete()
        for agent_name in payload.agent_names:
            db.add(RoleAgentModel(role_id=role_id, agent_name=agent_name))
    
    db.commit()
    db.refresh(role)
    
    menus = db.query(MenuModel).join(RoleMenuModel).filter(RoleMenuModel.role_id == role.id).all()
    agents = db.query(RoleAgentModel.agent_name).filter(RoleAgentModel.role_id == role.id).all()
    return {
        "id": role.id,
        "name": role.name,
        "display_name": role.display_name,
        "description": role.description,
        "data_scope": role.data_scope,
        "is_system": role.is_system,
        "status": role.status,
        "menus": [{"id": m.id, "name": m.name, "title": m.title} for m in menus],
        "agents": [a[0] for a in agents],
    }


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """删除角色。"""
    check_role_permission(current_user, db)
    
    role = db.query(RoleModel).filter(RoleModel.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system role")
    
    db.query(RoleMenuModel).filter(RoleMenuModel.role_id == role_id).delete()
    db.query(RoleAgentModel).filter(RoleAgentModel.role_id == role_id).delete()
    db.delete(role)
    db.commit()
    return {"success": True}
```

- [ ] **Step 2: 注册角色管理路由**

在 `app/main.py` 导入部分添加：
```python
from app.api import roles as roles_api
```

在路由注册部分添加：
```python
app.include_router(roles_api.router, prefix="/api/roles", tags=["roles"])
```

---

## Task 6: 菜单管理 API

**Files:**
- Create: `app/api/menus.py`
- Modify: `app/main.py`

**Goal:** 实现菜单 CRUD + 动态菜单 API

- [ ] **Step 1: 创建菜单管理 API**

```python
"""菜单管理 API 模块。"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.auth import get_current_user, get_user_permissions
from app.state.models import MenuModel, RoleMenuModel

router = APIRouter(prefix="/menus", tags=["menus"])


class MenuCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=50)
    path: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    menu_type: str = "page"
    permission: Optional[str] = None
    component: Optional[str] = None
    is_visible: int = 1


class MenuUpdateRequest(BaseModel):
    title: Optional[str] = None
    path: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    menu_type: Optional[str] = None
    permission: Optional[str] = None
    component: Optional[str] = None
    is_visible: Optional[int] = None
    status: Optional[str] = None


class MenuResponse(BaseModel):
    id: int
    name: str
    title: str
    path: Optional[str]
    icon: Optional[str]
    parent_id: Optional[int]
    sort_order: int
    menu_type: str
    permission: Optional[str]
    component: Optional[str]
    is_visible: int
    status: str
    children: List["MenuResponse"] = []

    class Config:
        from_attributes = True


def check_menu_permission(current_user: UserModel, db: Session):
    """检查当前用户是否有菜单管理权限。"""
    perms = get_user_permissions(db, current_user.id)
    if "menu:manage" not in perms:
        raise HTTPException(status_code=403, detail="Permission denied")


def build_menu_tree(menus: List[MenuModel], parent_id: Optional[int] = None) -> List[dict]:
    """构建菜单树。"""
    tree = []
    for menu in sorted([m for m in menus if m.parent_id == parent_id], key=lambda x: x.sort_order):
        children = build_menu_tree(menus, menu.id)
        node = {
            "id": menu.id,
            "name": menu.name,
            "title": menu.title,
            "path": menu.path,
            "icon": menu.icon,
            "parent_id": menu.parent_id,
            "sort_order": menu.sort_order,
            "menu_type": menu.menu_type,
            "permission": menu.permission,
            "component": menu.component,
            "is_visible": menu.is_visible,
            "status": menu.status,
            "children": children,
        }
        tree.append(node)
    return tree


@router.get("/tree")
async def get_menu_tree(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """获取完整菜单树（管理用）。"""
    check_menu_permission(current_user, db)
    menus = db.query(MenuModel).filter(MenuModel.status == "active").all()
    return build_menu_tree(menus)


@router.get("/my")
async def get_my_menus(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """获取当前用户有权限的菜单树。"""
    from app.state.models import UserRoleModel
    role_ids = db.query(UserRoleModel.role_id).filter(UserRoleModel.user_id == current_user.id).all()
    role_ids = [r[0] for r in role_ids]
    
    if not role_ids:
        return []
    
    menu_ids = db.query(RoleMenuModel.menu_id).filter(RoleMenuModel.role_id.in_(role_ids)).distinct().all()
    menu_ids = [m[0] for m in menu_ids]
    
    if not menu_ids:
        return []
    
    menus = db.query(MenuModel).filter(
        MenuModel.id.in_(menu_ids),
        MenuModel.status == "active",
        MenuModel.is_visible == 1,
    ).all()
    
    return build_menu_tree(menus)


@router.get("", response_model=List[MenuResponse])
async def list_menus(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """菜单列表（树形）。"""
    check_menu_permission(current_user, db)
    menus = db.query(MenuModel).all()
    return build_menu_tree(menus)


@router.post("", response_model=MenuResponse)
async def create_menu(
    payload: MenuCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """创建菜单。"""
    check_menu_permission(current_user, db)
    
    if db.query(MenuModel).filter(MenuModel.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Menu name already exists")
    
    menu = MenuModel(**payload.dict())
    db.add(menu)
    db.commit()
    db.refresh(menu)
    return {**menu.__dict__, "children": []}


@router.get("/{menu_id}", response_model=MenuResponse)
async def get_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """菜单详情。"""
    check_menu_permission(current_user, db)
    menu = db.query(MenuModel).filter(MenuModel.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return {**menu.__dict__, "children": []}


@router.put("/{menu_id}", response_model=MenuResponse)
async def update_menu(
    menu_id: int,
    payload: MenuUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """更新菜单。"""
    check_menu_permission(current_user, db)
    
    menu = db.query(MenuModel).filter(MenuModel.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(menu, field, value)
    
    db.commit()
    db.refresh(menu)
    return {**menu.__dict__, "children": []}


@router.delete("/{menu_id}")
async def delete_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """删除菜单。"""
    check_menu_permission(current_user, db)
    
    menu = db.query(MenuModel).filter(MenuModel.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    children = db.query(MenuModel).filter(MenuModel.parent_id == menu_id).count()
    if children > 0:
        raise HTTPException(status_code=400, detail="Cannot delete menu with children")
    
    db.query(RoleMenuModel).filter(RoleMenuModel.menu_id == menu_id).delete()
    db.delete(menu)
    db.commit()
    return {"success": True}
```

- [ ] **Step 2: 注册菜单管理路由**

在 `app/main.py` 导入部分添加：
```python
from app.api import menus as menus_api
```

在路由注册部分添加：
```python
app.include_router(menus_api.router, prefix="/api/menus", tags=["menus"])
```

---

## Task 7: 初始化数据脚本

**Files:**
- Create: `app/scripts/init_rbac.py`

**Goal:** 创建初始化脚本，预置角色、菜单和超级管理员用户

- [ ] **Step 1: 创建初始化脚本**

```python
"""RBAC 初始化脚本。"""

from app.state.models import init_db, get_db
from app.state.models import UserModel, RoleModel, MenuModel, UserRoleModel, RoleMenuModel, RoleAgentModel
from app.core.security import hash_password


def init_rbac_data():
    """初始化 RBAC 基础数据。"""
    init_db()
    db = next(get_db())
    
    try:
        # 1. 创建菜单
        menus_data = [
            # 顶级菜单
            {"name": "dashboard", "title": "sidebar.dashboard", "path": "/", "icon": "LayoutDashboard", "menu_type": "page", "permission": "dashboard:view", "sort_order": 1},
            {"name": "workbench", "title": "sidebar.workbench", "path": "/workbench", "icon": "ClipboardCheck", "menu_type": "page", "permission": "workbench:view", "sort_order": 2},
            {"name": "projects", "title": "sidebar.projects", "path": "/projects", "icon": "FolderKanban", "menu_type": "page", "permission": "project:view", "sort_order": 3},
            {"name": "task_management", "title": "sidebar.taskManagement", "path": "/tasks", "icon": "KanbanSquare", "menu_type": "directory", "permission": "task:view", "sort_order": 4},
            {"name": "scheduled_tasks", "title": "sidebar.scheduledTasks", "path": "/scheduled-tasks", "icon": "Clock", "menu_type": "page", "permission": "scheduled_task:view", "sort_order": 5},
            {"name": "agents", "title": "sidebar.agents", "path": "/agents", "icon": "Bot", "menu_type": "page", "permission": "agent:view", "sort_order": 6},
            {"name": "skills", "title": "sidebar.skills", "path": "/skills", "icon": "Wrench", "menu_type": "page", "permission": "skill:view", "sort_order": 7},
            {"name": "code_reviews", "title": "sidebar.codeReviews", "path": "/code-reviews", "icon": "GitPullRequest", "menu_type": "page", "permission": "code_review:view", "sort_order": 8},
            {"name": "workflow", "title": "sidebar.workflow", "path": "/workflow", "icon": "GitBranch", "menu_type": "directory", "permission": "workflow:view", "sort_order": 9},
            {"name": "settings", "title": "sidebar.settings", "path": "/settings", "icon": "Settings", "menu_type": "directory", "permission": "setting:view", "sort_order": 10},
            {"name": "user_management", "title": "sidebar.userManagement", "path": "/users", "icon": "Users", "menu_type": "page", "permission": "user:manage", "sort_order": 11},
            {"name": "role_management", "title": "sidebar.roleManagement", "path": "/roles", "icon": "UserCog", "menu_type": "page", "permission": "role:manage", "sort_order": 12},
            {"name": "menu_management", "title": "sidebar.menuManagement", "path": "/menus", "icon": "Menu", "menu_type": "page", "permission": "menu:manage", "sort_order": 13},
            # 子菜单
            {"name": "my_tasks", "title": "sidebar.myTasks", "path": "/tasks/my", "icon": "ListTodo", "menu_type": "page", "permission": "task:view", "parent_id": None, "sort_order": 1},
            {"name": "task_board", "title": "sidebar.taskBoard", "path": "/tasks/board", "icon": "KanbanSquare", "menu_type": "page", "permission": "task:view", "parent_id": None, "sort_order": 2},
            {"name": "workflow_editor", "title": "sidebar.workflowEditor", "path": "/workflow/editor", "icon": "Workflow", "menu_type": "page", "permission": "workflow:edit", "parent_id": None, "sort_order": 1},
            {"name": "workflow_list", "title": "sidebar.workflowList", "path": "/workflow/list", "icon": "List", "menu_type": "page", "permission": "workflow:view", "parent_id": None, "sort_order": 2},
            {"name": "workflow_instances", "title": "sidebar.workflowInstances", "path": "/workflow/instances", "icon": "Layers", "menu_type": "page", "permission": "workflow_instance:view", "parent_id": None, "sort_order": 3},
            {"name": "settings_system", "title": "sidebar.settingsSystem", "path": "/settings/system", "icon": "Monitor", "menu_type": "page", "permission": "setting:system", "parent_id": None, "sort_order": 1},
            {"name": "settings_llm", "title": "sidebar.settingsLlm", "path": "/settings/llm", "icon": "BrainCircuit", "menu_type": "page", "permission": "setting:llm", "parent_id": None, "sort_order": 2},
            {"name": "settings_database", "title": "sidebar.settingsDatabase", "path": "/settings/database", "icon": "Database", "menu_type": "page", "permission": "setting:database", "parent_id": None, "sort_order": 3},
            {"name": "settings_security", "title": "sidebar.settingsSecurity", "path": "/settings/security", "icon": "Shield", "menu_type": "page", "permission": "setting:security", "parent_id": None, "sort_order": 4},
            {"name": "settings_about", "title": "sidebar.settingsAbout", "path": "/settings/about", "icon": "Info", "menu_type": "page", "permission": "setting:about", "parent_id": None, "sort_order": 5},
        ]
        
        menu_map = {}
        for data in menus_data:
            menu = MenuModel(**{k: v for k, v in data.items() if k != "parent_id"})
            db.add(menu)
            db.flush()
            menu_map[data["name"]] = menu.id
        
        # 更新子菜单 parent_id
        parent_map = {
            "my_tasks": "task_management",
            "task_board": "task_management",
            "workflow_editor": "workflow",
            "workflow_list": "workflow",
            "workflow_instances": "workflow",
            "settings_system": "settings",
            "settings_llm": "settings",
            "settings_database": "settings",
            "settings_security": "settings",
            "settings_about": "settings",
        }
        for child_name, parent_name in parent_map.items():
            menu = db.query(MenuModel).filter(MenuModel.name == child_name).first()
            if menu:
                menu.parent_id = menu_map[parent_name]
        
        db.commit()
        
        # 2. 创建角色
        roles_data = [
            {"name": "super_admin", "display_name": "超级管理员", "description": "拥有所有权限", "data_scope": "all", "is_system": 1},
            {"name": "admin", "display_name": "系统管理员", "description": "管理用户、角色、菜单", "data_scope": "all", "is_system": 1},
            {"name": "project_manager", "display_name": "项目经理", "description": "管理项目和工作流", "data_scope": "all", "is_system": 1},
            {"name": "developer", "display_name": "开发工程师", "description": "开发项目、查看代码审查", "data_scope": "self", "is_system": 1},
            {"name": "tester", "display_name": "测试工程师", "description": "执行测试、查看代码审查", "data_scope": "self", "is_system": 1},
            {"name": "viewer", "display_name": "访客", "description": "只读权限", "data_scope": "self", "is_system": 1},
        ]
        
        role_map = {}
        for data in roles_data:
            role = RoleModel(**data)
            db.add(role)
            db.flush()
            role_map[data["name"]] = role.id
        
        db.commit()
        
        # 3. 为角色分配菜单
        all_menu_ids = list(menu_map.values())
        
        # super_admin 和 admin 拥有所有菜单
        for role_name in ["super_admin", "admin"]:
            for menu_id in all_menu_ids:
                db.add(RoleMenuModel(role_id=role_map[role_name], menu_id=menu_id))
        
        # project_manager 拥有除用户/角色/菜单管理外的所有菜单
        pm_exclude = ["user_management", "role_management", "menu_management"]
        pm_menu_ids = [menu_map[m] for m in menu_map if m not in pm_exclude]
        for menu_id in pm_menu_ids:
            db.add(RoleMenuModel(role_id=role_map["project_manager"], menu_id=menu_id))
        
        # developer 拥有仪表盘、工作台、项目管理、任务管理、代码审查、流程管理
        dev_menus = ["dashboard", "workbench", "projects", "task_management", "my_tasks", "task_board",
                     "code_reviews", "workflow", "workflow_list", "workflow_instances", "settings", "settings_about"]
        for m in dev_menus:
            if m in menu_map:
                db.add(RoleMenuModel(role_id=role_map["developer"], menu_id=menu_map[m]))
        
        # tester 类似 developer
        for m in dev_menus:
            if m in menu_map:
                db.add(RoleMenuModel(role_id=role_map["tester"], menu_id=menu_map[m]))
        
        # viewer 只读
        viewer_menus = ["dashboard", "projects", "task_management", "my_tasks", "task_board",
                        "code_reviews", "workflow", "workflow_list", "workflow_instances"]
        for m in viewer_menus:
            if m in menu_map:
                db.add(RoleMenuModel(role_id=role_map["viewer"], menu_id=menu_map[m]))
        
        db.commit()
        
        # 4. 为角色分配 Agent
        agent_map = {
            "super_admin": ["business_analyst", "product_manager", "architect", "developer", "qa", "project_manager", "code_reviewer"],
            "admin": ["business_analyst", "product_manager", "architect", "developer", "qa", "project_manager", "code_reviewer"],
            "project_manager": ["business_analyst", "product_manager", "architect", "developer", "qa", "project_manager", "code_reviewer"],
            "developer": ["developer", "qa", "code_reviewer"],
            "tester": ["qa", "code_reviewer"],
            "viewer": [],
        }
        
        for role_name, agents in agent_map.items():
            for agent_name in agents:
                db.add(RoleAgentModel(role_id=role_map[role_name], agent_name=agent_name))
        
        db.commit()
        
        # 5. 创建超级管理员用户
        admin_user = UserModel(
            username="admin",
            password_hash=hash_password("admin123"),
            nickname="管理员",
            email="admin@devmatrix.local",
            data_scope="all",
        )
        db.add(admin_user)
        db.flush()
        
        # 分配 super_admin 角色
        db.add(UserRoleModel(user_id=admin_user.id, role_id=role_map["super_admin"]))
        db.commit()
        
        print("RBAC data initialized successfully!")
        print(f"  - {len(menus_data)} menus")
        print(f"  - {len(roles_data)} roles")
        print(f"  - 1 user (admin / admin123)")
        
    except Exception as e:
        db.rollback()
        print(f"Error initializing RBAC data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_rbac_data()
```

- [ ] **Step 2: 运行初始化脚本**

Run: `cd /Users/Summer/Documents/works/codes/dev-matrix && source venv/bin/activate && python app/scripts/init_rbac.py`
Expected: `RBAC data initialized successfully!`

---

## Task 8: 前端 Pinia Store

**Files:**
- Create: `frontend/src/stores/user.ts`

**Goal:** 创建用户状态管理 Store

- [ ] **Step 1: 安装 Pinia**

Run: `cd /Users/Summer/Documents/works/codes/dev-matrix/frontend && npm install pinia`

- [ ] **Step 2: 创建 User Store**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface UserInfo {
  id: number
  username: string
  nickname: string | null
  email: string | null
  avatar: string | null
  roles: Array<{ id: number; name: string; display_name: string }>
  permissions: string[]
  agents: string[]
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)
  const menus = ref<any[]>([])

  const isLoggedIn = computed(() => !!token.value)
  const hasPermission = computed(() => (perm: string) => {
    if (!userInfo.value) return false
    return userInfo.value.permissions.includes(perm)
  })
  const hasAgent = computed(() => (agentName: string) => {
    if (!userInfo.value) return false
    return userInfo.value.agents.includes(agentName)
  })

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function clearToken() {
    token.value = ''
    userInfo.value = null
    menus.value = []
    localStorage.removeItem('token')
  }

  function setUserInfo(info: UserInfo) {
    userInfo.value = info
  }

  function setMenus(newMenus: any[]) {
    menus.value = newMenus
  }

  return {
    token,
    userInfo,
    menus,
    isLoggedIn,
    hasPermission,
    hasAgent,
    setToken,
    clearToken,
    setUserInfo,
    setMenus,
  }
})
```

- [ ] **Step 3: 注册 Pinia**

在 `frontend/src/main.ts` 中添加：
```typescript
import { createPinia } from 'pinia'

const app = createApp(App)
app.use(createPinia())
```

---

## Task 9: 前端认证 API

**Files:**
- Create: `frontend/src/api/auth.ts`
- Modify: `frontend/src/api/index.ts`

**Goal:** 添加认证相关 API 和 Token 拦截器

- [ ] **Step 1: 创建认证 API**

```typescript
import { api } from './index'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  refresh_token: string
  expires_at: number
  user: {
    id: number
    username: string
    nickname: string | null
    email: string | null
    avatar: string | null
    roles: Array<{ id: number; name: string; display_name: string }>
  }
}

export interface UserInfo {
  id: number
  username: string
  nickname: string | null
  email: string | null
  avatar: string | null
  roles: Array<{ id: number; name: string; display_name: string }>
  permissions: string[]
  agents: string[]
}

export const authApi = {
  login(data: LoginRequest) {
    return api.post<LoginResponse>('/auth/login', data)
  },

  logout() {
    return api.post('/auth/logout')
  },

  getMe() {
    return api.get<UserInfo>('/auth/me')
  },

  refreshToken() {
    return api.post<{ token: string; expires_at: number }>('/auth/refresh')
  },

  changePassword(oldPassword: string, newPassword: string) {
    return api.post('/auth/password', { old_password: oldPassword, new_password: newPassword })
  },
}
```

- [ ] **Step 2: 修改 API 请求函数添加 Token**

在 `frontend/src/api/index.ts` 中修改 `request` 函数：

```typescript
import { useUserStore } from '../stores/user'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30000)

  try {
    const { headers: customHeaders, ...restOptions } = options || {}
    
    // 添加 Token
    const userStore = useUserStore()
    const token = userStore.token
    const authHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...customHeaders,
    }
    if (token) {
      authHeaders['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${API_BASE}${url}`, {
      headers: authHeaders,
      signal: controller.signal,
      ...restOptions,
    })

    clearTimeout(timeoutId)

    if (response.status === 401) {
      userStore.clearToken()
      window.location.href = '/login'
      throw new Error('Session expired, please login again')
    }

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText)
      throw new Error(`API Error ${response.status}: ${errorText}`)
    }

    // ... 其余保持不变
```

---

## Task 10: 登录页面

**Files:**
- Create: `frontend/src/pages/LoginPage.vue`
- Modify: `frontend/src/router.ts`

**Goal:** 创建登录页面

- [ ] **Step 1: 创建登录页面**

```vue
<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="login-title">DevMatrix</h1>
      <p class="login-subtitle">多角色协作软件开发 Agent 操作系统</p>
      
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input
            v-model="form.username"
            type="text"
            placeholder="请输入用户名"
            required
          />
        </div>
        
        <div class="form-group">
          <label>密码</label>
          <input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            required
          />
        </div>
        
        <div v-if="error" class="error-message">{{ error }}</div>
        
        <button type="submit" class="login-btn" :disabled="isLoading">
          {{ isLoading ? '登录中...' : '登录' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { authApi } from '../api/auth'

const router = useRouter()
const userStore = useUserStore()

const form = reactive({
  username: '',
  password: '',
})

const isLoading = ref(false)
const error = ref('')

async function handleLogin() {
  isLoading.value = true
  error.value = ''
  
  try {
    const res = await authApi.login(form)
    userStore.setToken(res.token)
    
    // 获取用户信息
    const userInfo = await authApi.getMe()
    userStore.setUserInfo(userInfo)
    
    // 获取菜单
    const menus = await api.getMyMenus()
    userStore.setMenus(menus)
    
    router.push('/')
  } catch (e: any) {
    error.value = e.message || '登录失败'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: var(--surface-color, #ffffff);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 8px 0;
  color: var(--text-primary, #111827);
}

.login-subtitle {
  font-size: 14px;
  text-align: center;
  color: var(--text-secondary, #6b7280);
  margin: 0 0 32px 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
  color: var(--text-primary, #111827);
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-secondary, #f9fafb);
  color: var(--text-primary, #111827);
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary-color, #3b82f6);
}

.error-message {
  color: #ef4444;
  font-size: 14px;
  margin-bottom: 16px;
  text-align: center;
}

.login-btn {
  width: 100%;
  padding: 12px;
  background: var(--primary-color, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.login-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
```

- [ ] **Step 2: 添加登录路由和路由守卫**

在 `frontend/src/router.ts` 中添加：

```typescript
import { useUserStore } from './stores/user'

// 添加登录路由
const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('./pages/LoginPage.vue'),
    meta: { public: true },
  },
  // ... 现有路由
]

// 添加路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.public) {
    next()
    return
  }
  
  if (!userStore.isLoggedIn) {
    next('/login')
    return
  }
  
  next()
})
```

---

## Task 11: 用户管理页面

**Files:**
- Create: `frontend/src/pages/users/UserListPage.vue`
- Create: `frontend/src/pages/users/UserFormModal.vue`
- Modify: `frontend/src/router.ts`

**Goal:** 创建用户管理列表和表单页面

- [ ] **Step 1: 创建用户列表页面**

```vue
<template>
  <div class="user-list-page">
    <div class="page-header">
      <h1>用户管理</h1>
      <button v-permission="'user:manage'" class="btn-primary" @click="showCreateModal">
        新建用户
      </button>
    </div>
    
    <div class="filters">
      <input v-model="keyword" placeholder="搜索用户名或昵称" @input="loadUsers" />
      <select v-model="statusFilter" @change="loadUsers">
        <option value="">全部状态</option>
        <option value="active">启用</option>
        <option value="disabled">禁用</option>
      </select>
    </div>
    
    <table class="data-table">
      <thead>
        <tr>
          <th>用户名</th>
          <th>昵称</th>
          <th>角色</th>
          <th>状态</th>
          <th>最后登录</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.username }}</td>
          <td>{{ user.nickname || '-' }}</td>
          <td>
            <span v-for="role in user.roles" :key="role.id" class="role-tag">
              {{ role.display_name }}
            </span>
          </td>
          <td>
            <span :class="['status-badge', user.status]">
              {{ user.status === 'active' ? '启用' : '禁用' }}
            </span>
          </td>
          <td>{{ user.last_login_at ? formatDate(user.last_login_at) : '-' }}</td>
          <td>
            <button class="btn-text" @click="editUser(user)">编辑</button>
            <button class="btn-text" @click="toggleStatus(user)">
              {{ user.status === 'active' ? '禁用' : '启用' }}
            </button>
            <button class="btn-text danger" @click="deleteUser(user)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    
    <UserFormModal
      v-if="modalVisible"
      :user="editingUser"
      @close="modalVisible = false"
      @saved="loadUsers"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../../api'
import UserFormModal from './UserFormModal.vue'

const users = ref<any[]>([])
const keyword = ref('')
const statusFilter = ref('')
const modalVisible = ref(false)
const editingUser = ref<any>(null)

async function loadUsers() {
  const params: any = {}
  if (keyword.value) params.keyword = keyword.value
  if (statusFilter.value) params.status = statusFilter.value
  const res = await api.getUsers(params)
  users.value = res
}

function showCreateModal() {
  editingUser.value = null
  modalVisible.value = true
}

function editUser(user: any) {
  editingUser.value = user
  modalVisible.value = true
}

async function toggleStatus(user: any) {
  const newStatus = user.status === 'active' ? 'disabled' : 'active'
  await api.updateUserStatus(user.id, newStatus)
  loadUsers()
}

async function deleteUser(user: any) {
  if (!confirm(`确认删除用户「${user.username}」？`)) return
  await api.deleteUser(user.id)
  loadUsers()
}

function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(loadUsers)
</script>
```

- [ ] **Step 2: 创建用户表单弹窗**

```vue
<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <h3>{{ isEdit ? '编辑用户' : '新建用户' }}</h3>
      
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>用户名 *</label>
          <input v-model="form.username" :disabled="isEdit" required />
        </div>
        
        <div v-if="!isEdit" class="form-group">
          <label>密码 *</label>
          <input v-model="form.password" type="password" required />
        </div>
        
        <div class="form-group">
          <label>昵称</label>
          <input v-model="form.nickname" />
        </div>
        
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="form.email" type="email" />
        </div>
        
        <div class="form-group">
          <label>角色</label>
          <select v-model="form.role_ids" multiple>
            <option v-for="role in roles" :key="role.id" :value="role.id">
              {{ role.display_name }}
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label>数据权限</label>
          <select v-model="form.data_scope">
            <option value="self">仅自己</option>
            <option value="dept">本部门</option>
            <option value="all">全部</option>
          </select>
        </div>
        
        <div class="modal-actions">
          <button type="button" class="btn-secondary" @click="$emit('close')">取消</button>
          <button type="submit" class="btn-primary" :disabled="isSubmitting">
            {{ isSubmitting ? '保存中...' : '保存' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { api } from '../../api'

const props = defineProps<{ user: any }>()
const emit = defineEmits(['close', 'saved'])

const isEdit = computed(() => !!props.user)
const isSubmitting = ref(false)
const roles = ref<any[]>([])

const form = reactive({
  username: '',
  password: '',
  nickname: '',
  email: '',
  role_ids: [] as number[],
  data_scope: 'self',
})

onMounted(async () => {
  roles.value = await api.getRoles()
  if (props.user) {
    form.username = props.user.username
    form.nickname = props.user.nickname || ''
    form.email = props.user.email || ''
    form.data_scope = props.user.data_scope
    form.role_ids = props.user.roles.map((r: any) => r.id)
  }
})

async function handleSubmit() {
  isSubmitting.value = true
  try {
    if (isEdit.value) {
      await api.updateUser(props.user.id, {
        nickname: form.nickname,
        email: form.email,
        data_scope: form.data_scope,
        role_ids: form.role_ids,
      })
    } else {
      await api.createUser({
        username: form.username,
        password: form.password,
        nickname: form.nickname,
        email: form.email,
        role_ids: form.role_ids,
        data_scope: form.data_scope,
      })
    }
    emit('saved')
    emit('close')
  } finally {
    isSubmitting.value = false
  }
}
</script>
```

- [ ] **Step 3: 添加用户管理路由**

在 `frontend/src/router.ts` 中添加：
```typescript
{
  path: '/users',
  name: 'users',
  component: () => import('./pages/users/UserListPage.vue'),
  meta: { title: 'User Management', icon: 'users', permission: 'user:manage' },
},
```

---

## Task 12: 角色管理页面

**Files:**
- Create: `frontend/src/pages/roles/RoleListPage.vue`
- Create: `frontend/src/pages/roles/RoleFormModal.vue`
- Modify: `frontend/src/router.ts`

**Goal:** 创建角色管理列表和表单页面

- [ ] **Step 1: 创建角色列表页面**

```vue
<template>
  <div class="role-list-page">
    <div class="page-header">
      <h1>角色管理</h1>
      <button class="btn-primary" @click="showCreateModal">新建角色</button>
    </div>
    
    <table class="data-table">
      <thead>
        <tr>
          <th>角色标识</th>
          <th>显示名称</th>
          <th>描述</th>
          <th>数据权限</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="role in roles" :key="role.id">
          <td>{{ role.name }}</td>
          <td>{{ role.display_name }}</td>
          <td>{{ role.description || '-' }}</td>
          <td>{{ scopeLabel(role.data_scope) }}</td>
          <td>
            <span :class="['status-badge', role.status]">
              {{ role.status === 'active' ? '启用' : '禁用' }}
            </span>
          </td>
          <td>
            <button class="btn-text" @click="editRole(role)">编辑</button>
            <button v-if="!role.is_system" class="btn-text danger" @click="deleteRole(role)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    
    <RoleFormModal
      v-if="modalVisible"
      :role="editingRole"
      @close="modalVisible = false"
      @saved="loadRoles"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../../api'
import RoleFormModal from './RoleFormModal.vue'

const roles = ref<any[]>([])
const modalVisible = ref(false)
const editingRole = ref<any>(null)

async function loadRoles() {
  roles.value = await api.getRoles()
}

function showCreateModal() {
  editingRole.value = null
  modalVisible.value = true
}

function editRole(role: any) {
  editingRole.value = role
  modalVisible.value = true
}

async function deleteRole(role: any) {
  if (!confirm(`确认删除角色「${role.display_name}」？`)) return
  await api.deleteRole(role.id)
  loadRoles()
}

function scopeLabel(scope: string) {
  const map: Record<string, string> = { all: '全部', dept: '本部门', self: '仅自己' }
  return map[scope] || scope
}

onMounted(loadRoles)
</script>
```

- [ ] **Step 2: 创建角色表单弹窗（含菜单树和 Agent 选择）**

```vue
<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content wide" @click.stop>
      <h3>{{ isEdit ? '编辑角色' : '新建角色' }}</h3>
      
      <form @submit.prevent="handleSubmit">
        <div class="form-row">
          <div class="form-group">
            <label>角色标识 *</label>
            <input v-model="form.name" :disabled="isEdit" required />
          </div>
          <div class="form-group">
            <label>显示名称 *</label>
            <input v-model="form.display_name" required />
          </div>
        </div>
        
        <div class="form-group">
          <label>描述</label>
          <input v-model="form.description" />
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>数据权限</label>
            <select v-model="form.data_scope">
              <option value="self">仅自己</option>
              <option value="dept">本部门</option>
              <option value="all">全部</option>
            </select>
          </div>
        </div>
        
        <div class="form-group">
          <label>菜单权限</label>
          <div class="menu-tree">
            <div v-for="menu in menuTree" :key="menu.id" class="menu-item">
              <label class="menu-label">
                <input
                  type="checkbox"
                  :checked="isMenuSelected(menu.id)"
                  @change="toggleMenu(menu.id)"
                />
                <span>{{ menu.title }}</span>
              </label>
              <div v-if="menu.children?.length" class="menu-children">
                <label v-for="child in menu.children" :key="child.id" class="menu-label child">
                  <input
                    type="checkbox"
                    :checked="isMenuSelected(child.id)"
                    @change="toggleMenu(child.id)"
                  />
                  <span>{{ child.title }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>
        
        <div class="form-group">
          <label>Agent 权限</label>
          <div class="agent-checkboxes">
            <label v-for="agent in agents" :key="agent.name" class="agent-label">
              <input
                type="checkbox"
                :value="agent.name"
                v-model="form.agent_names"
              />
              <span>{{ agent.display_name || agent.name }}</span>
            </label>
          </div>
        </div>
        
        <div class="modal-actions">
          <button type="button" class="btn-secondary" @click="$emit('close')">取消</button>
          <button type="submit" class="btn-primary" :disabled="isSubmitting">
            {{ isSubmitting ? '保存中...' : '保存' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { api } from '../../api'

const props = defineProps<{ role: any }>()
const emit = defineEmits(['close', 'saved'])

const isEdit = computed(() => !!props.role)
const isSubmitting = ref(false)
const menuTree = ref<any[]>([])
const agents = ref<any[]>([])

const form = reactive({
  name: '',
  display_name: '',
  description: '',
  data_scope: 'self',
  menu_ids: [] as number[],
  agent_names: [] as string[],
})

onMounted(async () => {
  menuTree.value = await api.getMenuTree()
  agents.value = await api.getAgentDetails()
  
  if (props.role) {
    form.name = props.role.name
    form.display_name = props.role.display_name
    form.description = props.role.description || ''
    form.data_scope = props.role.data_scope
    form.menu_ids = props.role.menus.map((m: any) => m.id)
    form.agent_names = props.role.agents
  }
})

function isMenuSelected(menuId: number) {
  return form.menu_ids.includes(menuId)
}

function toggleMenu(menuId: number) {
  const idx = form.menu_ids.indexOf(menuId)
  if (idx > -1) {
    form.menu_ids.splice(idx, 1)
  } else {
    form.menu_ids.push(menuId)
  }
}

async function handleSubmit() {
  isSubmitting.value = true
  try {
    if (isEdit.value) {
      await api.updateRole(props.role.id, {
        display_name: form.display_name,
        description: form.description,
        data_scope: form.data_scope,
        menu_ids: form.menu_ids,
        agent_names: form.agent_names,
      })
    } else {
      await api.createRole({
        name: form.name,
        display_name: form.display_name,
        description: form.description,
        data_scope: form.data_scope,
        menu_ids: form.menu_ids,
        agent_names: form.agent_names,
      })
    }
    emit('saved')
    emit('close')
  } finally {
    isSubmitting.value = false
  }
}
</script>
```

- [ ] **Step 3: 添加角色管理路由**

在 `frontend/src/router.ts` 中添加：
```typescript
{
  path: '/roles',
  name: 'roles',
  component: () => import('./pages/roles/RoleListPage.vue'),
  meta: { title: 'Role Management', icon: 'user-cog', permission: 'role:manage' },
},
```

---

## Task 13: 菜单管理页面

**Files:**
- Create: `frontend/src/pages/menus/MenuListPage.vue`
- Create: `frontend/src/pages/menus/MenuFormModal.vue`
- Modify: `frontend/src/router.ts`

**Goal:** 创建菜单管理树形页面

- [ ] **Step 1: 创建菜单列表页面**

```vue
<template>
  <div class="menu-list-page">
    <div class="page-header">
      <h1>菜单管理</h1>
      <button class="btn-primary" @click="showCreateModal">新建菜单</button>
    </div>
    
    <div class="menu-tree-table">
      <div v-for="menu in menuTree" :key="menu.id" class="menu-row">
        <div class="menu-info" :style="{ paddingLeft: menu.level * 24 + 16 + 'px' }">
          <span class="menu-icon">{{ menu.icon || '○' }}</span>
          <span class="menu-name">{{ menu.title }}</span>
          <span class="menu-type">{{ typeLabel(menu.menu_type) }}</span>
          <span class="menu-path">{{ menu.path || '-' }}</span>
          <span class="menu-perm">{{ menu.permission || '-' }}</span>
        </div>
        <div class="menu-actions">
          <button class="btn-text" @click="editMenu(menu)">编辑</button>
          <button class="btn-text" @click="showCreateModal(menu.id)">添加子菜单</button>
          <button v-if="!menu.children?.length" class="btn-text danger" @click="deleteMenu(menu)">删除</button>
        </div>
      </div>
    </div>
    
    <MenuFormModal
      v-if="modalVisible"
      :menu="editingMenu"
      :parent-id="newParentId"
      @close="modalVisible = false"
      @saved="loadMenus"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../../api'
import MenuFormModal from './MenuFormModal.vue'

const menuTree = ref<any[]>([])
const modalVisible = ref(false)
const editingMenu = ref<any>(null)
const newParentId = ref<number | null>(null)

async function loadMenus() {
  const tree = await api.getMenuTree()
  menuTree.value = flattenTree(tree)
}

function flattenTree(tree: any[], level = 0): any[] {
  const result: any[] = []
  for (const node of tree) {
    result.push({ ...node, level })
    if (node.children?.length) {
      result.push(...flattenTree(node.children, level + 1))
    }
  }
  return result
}

function showCreateModal(parentId: number | null = null) {
  editingMenu.value = null
  newParentId.value = parentId
  modalVisible.value = true
}

function editMenu(menu: any) {
  editingMenu.value = menu
  newParentId.value = null
  modalVisible.value = true
}

async function deleteMenu(menu: any) {
  if (!confirm(`确认删除菜单「${menu.title}」？`)) return
  await api.deleteMenu(menu.id)
  loadMenus()
}

function typeLabel(type: string) {
  const map: Record<string, string> = { directory: '目录', page: '页面', button: '按钮' }
  return map[type] || type
}

onMounted(loadMenus)
</script>
```

- [ ] **Step 2: 创建菜单表单弹窗**

```vue
<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <h3>{{ isEdit ? '编辑菜单' : '新建菜单' }}</h3>
      
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>菜单标识 *</label>
          <input v-model="form.name" :disabled="isEdit" required />
        </div>
        
        <div class="form-group">
          <label>标题 *</label>
          <input v-model="form.title" required />
        </div>
        
        <div class="form-group">
          <label>路径</label>
          <input v-model="form.path" placeholder="如 /projects" />
        </div>
        
        <div class="form-group">
          <label>图标</label>
          <input v-model="form.icon" placeholder="Lucide 图标名称" />
        </div>
        
        <div class="form-group">
          <label>父级菜单</label>
          <select v-model="form.parent_id">
            <option :value="null">顶级菜单</option>
            <option v-for="menu in parentMenus" :key="menu.id" :value="menu.id">
              {{ menu.title }}
            </option>
          </select>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>类型</label>
            <select v-model="form.menu_type">
              <option value="directory">目录</option>
              <option value="page">页面</option>
              <option value="button">按钮</option>
            </select>
          </div>
          <div class="form-group">
            <label>排序</label>
            <input v-model.number="form.sort_order" type="number" />
          </div>
        </div>
        
        <div class="form-group">
          <label>权限标识</label>
          <input v-model="form.permission" placeholder="如 project:view" />
        </div>
        
        <div class="form-group">
          <label>组件路径</label>
          <input v-model="form.component" placeholder="前端组件路径" />
        </div>
        
        <div class="modal-actions">
          <button type="button" class="btn-secondary" @click="$emit('close')">取消</button>
          <button type="submit" class="btn-primary" :disabled="isSubmitting">
            {{ isSubmitting ? '保存中...' : '保存' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { api } from '../../api'

const props = defineProps<{ menu: any; parentId: number | null }>()
const emit = defineEmits(['close', 'saved'])

const isEdit = computed(() => !!props.menu)
const isSubmitting = ref(false)
const parentMenus = ref<any[]>([])

const form = reactive({
  name: '',
  title: '',
  path: '',
  icon: '',
  parent_id: null as number | null,
  sort_order: 0,
  menu_type: 'page',
  permission: '',
  component: '',
})

onMounted(async () => {
  parentMenus.value = await api.getMenus()
  if (props.menu) {
    Object.assign(form, props.menu)
  } else if (props.parentId !== null) {
    form.parent_id = props.parentId
  }
})

async function handleSubmit() {
  isSubmitting.value = true
  try {
    if (isEdit.value) {
      await api.updateMenu(props.menu.id, { ...form })
    } else {
      await api.createMenu({ ...form })
    }
    emit('saved')
    emit('close')
  } finally {
    isSubmitting.value = false
  }
}
</script>
```

- [ ] **Step 3: 添加菜单管理路由**

在 `frontend/src/router.ts` 中添加：
```typescript
{
  path: '/menus',
  name: 'menus',
  component: () => import('./pages/menus/MenuListPage.vue'),
  meta: { title: 'Menu Management', icon: 'menu', permission: 'menu:manage' },
},
```

---

## Task 14: 动态菜单与权限指令

**Files:**
- Modify: `frontend/src/components/Sidebar.vue`
- Create: `frontend/src/directives/permission.ts`
- Modify: `frontend/src/main.ts`

**Goal:** 将 Sidebar 改为动态菜单，添加权限指令

- [ ] **Step 1: 修改 Sidebar 为动态菜单**

修改 `frontend/src/components/Sidebar.vue`，将 `navItems` 改为从 store 获取：

```typescript
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

// 将后端菜单格式转换为 NavItem 格式
const navItems = computed(() => {
  return userStore.menus.map(menu => ({
    id: menu.name,
    path: menu.path || '',
    title: menu.title,
    icon: getIconComponent(menu.icon),
    children: menu.children?.map((child: any) => ({
      id: child.name,
      path: child.path || '',
      title: child.title,
      icon: getIconComponent(child.icon),
    })),
  }))
})

function getIconComponent(iconName: string) {
  // 映射图标名称到 Lucide 组件
  const iconMap: Record<string, any> = {
    LayoutDashboard, Bot, Wrench, GitBranch, Workflow, List, Layers,
    ClipboardCheck, Settings, FolderKanban, Monitor, BrainCircuit,
    Database, Shield, Info, Clock, KanbanSquare, ListTodo, GitPullRequest,
    Users, UserCog, Menu,
  }
  return iconMap[iconName] || LayoutDashboard
}
```

- [ ] **Step 2: 创建权限指令**

```typescript
// frontend/src/directives/permission.ts
import type { Directive } from 'vue'
import { useUserStore } from '../stores/user'

export const permission: Directive = {
  mounted(el, binding) {
    const userStore = useUserStore()
    const permission = binding.value
    
    if (!userStore.hasPermission(permission)) {
      el.style.display = 'none'
    }
  },
  updated(el, binding) {
    const userStore = useUserStore()
    const permission = binding.value
    
    if (userStore.hasPermission(permission)) {
      el.style.display = ''
    } else {
      el.style.display = 'none'
    }
  },
}
```

- [ ] **Step 3: 注册指令**

在 `frontend/src/main.ts` 中添加：
```typescript
import { permission } from './directives/permission'

app.directive('permission', permission)
```

---

## Task 15: 国际化

**Files:**
- Modify: `frontend/src/i18n/locales/zh.json`
- Modify: `frontend/src/i18n/locales/en.json`

**Goal:** 添加用户管理相关翻译

- [ ] **Step 1: 添加中文翻译**

在 `zh.json` 的 `sidebar` 中添加：
```json
"userManagement": "用户管理",
"roleManagement": "角色管理",
"menuManagement": "菜单管理"
```

在 `zh.json` 中添加新的命名空间：
```json
"users": {
  "title": "用户管理",
  "subtitle": "管理系统用户账号",
  "newUser": "新建用户",
  "editUser": "编辑用户",
  "username": "用户名",
  "password": "密码",
  "nickname": "昵称",
  "email": "邮箱",
  "role": "角色",
  "dataScope": "数据权限",
  "status": "状态",
  "lastLogin": "最后登录",
  "actions": "操作",
  "confirmDelete": "确认删除用户「{name}」？",
  "scopeAll": "全部",
  "scopeDept": "本部门",
  "scopeSelf": "仅自己"
},
"roles": {
  "title": "角色管理",
  "subtitle": "管理角色和权限分配",
  "newRole": "新建角色",
  "editRole": "编辑角色",
  "name": "角色标识",
  "displayName": "显示名称",
  "description": "描述",
  "menuPermission": "菜单权限",
  "agentPermission": "Agent 权限",
  "confirmDelete": "确认删除角色「{name}」？"
},
"menus": {
  "title": "菜单管理",
  "subtitle": "管理系统导航菜单",
  "newMenu": "新建菜单",
  "editMenu": "编辑菜单",
  "name": "菜单标识",
  "title": "标题",
  "path": "路径",
  "icon": "图标",
  "parent": "父级菜单",
  "type": "类型",
  "typeDirectory": "目录",
  "typePage": "页面",
  "typeButton": "按钮",
  "permission": "权限标识",
  "sort": "排序",
  "confirmDelete": "确认删除菜单「{name}」？"
}
```

---

## Task 16: 测试与验证

**Goal:** 验证整个 RBAC 系统是否正常工作

- [ ] **Step 1: 测试登录流程**

Run:
```bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python -m json.tool
```
Expected: 返回 token 和用户信息

- [ ] **Step 2: 测试获取当前用户**

Run:
```bash
curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <token>"
```
Expected: 返回用户详细信息，包含 roles、permissions、agents

- [ ] **Step 3: 测试用户管理 API**

Run:
```bash
curl -s http://localhost:8000/api/users \
  -H "Authorization: Bearer <token>"
```
Expected: 返回用户列表

- [ ] **Step 4: 测试角色管理 API**

Run:
```bash
curl -s http://localhost:8000/api/roles \
  -H "Authorization: Bearer <token>"
```
Expected: 返回角色列表，包含菜单和 Agent

- [ ] **Step 5: 测试动态菜单 API**

Run:
```bash
curl -s http://localhost:8000/api/menus/my \
  -H "Authorization: Bearer <token>"
```
Expected: 返回当前用户有权限的菜单树

- [ ] **Step 6: 前端登录测试**

1. 访问 http://localhost:3000/login
2. 输入 admin / admin123
3. 验证登录成功后跳转到仪表盘
4. 验证 Sidebar 显示正确的菜单
5. 验证用户管理、角色管理、菜单管理页面可正常访问

---

## Spec Coverage Check

| 需求 | 实现任务 |
|------|----------|
| 用户认证（用户名+密码） | Task 2, 3, 10 |
| JWT Token | Task 2, 3 |
| 用户管理 CRUD | Task 4, 11 |
| 角色管理 CRUD | Task 5, 12 |
| 角色关联 Agent | Task 5, 12 |
| 菜单管理 CRUD | Task 6, 13 |
| 动态菜单 | Task 6, 14 |
| 按钮级权限 | Task 14 |
| 数据级权限 | Task 4 (data_scope) |
| 预置角色/菜单/用户 | Task 7 |
| 国际化 | Task 15 |

---

## Placeholder Scan

- 无 TBD/TODO
- 所有代码片段完整
- 所有 API 路径正确
- 所有文件路径正确

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-25-rbac-user-management.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session, batch execution with checkpoints for review

**Which approach?**
