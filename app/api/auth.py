"""认证 API 模块。

提供登录、登出、当前用户信息、刷新 Token、修改密码等认证相关接口。

主要路由：
    - POST /auth/login: 用户登录
    - POST /auth/logout: 用户登出
    - GET /auth/me: 获取当前用户信息
    - POST /auth/refresh: 刷新 Access Token
    - POST /auth/password: 修改密码
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.state.models import UserModel, RoleModel, UserRoleModel, MenuModel, RoleMenuModel, RoleAgentModel
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token

router = APIRouter(tags=["auth"])


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
    payload = decode_token(db, token)
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

    token = create_access_token(db, {"sub": str(user.id), "username": user.username})
    refresh = create_refresh_token(db, {"sub": str(user.id)})

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
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    """刷新 Access Token。"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing refresh token")

    token = auth_header[7:]
    payload = decode_token(db, token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_token = create_access_token(db, {"sub": payload["sub"], "username": payload.get("username", "")})
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
