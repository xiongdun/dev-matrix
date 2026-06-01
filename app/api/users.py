"""用户管理 API 模块。

提供用户列表、创建、详情、更新、删除、状态切换等管理接口。

主要路由：
    - GET /users: 用户列表
    - POST /users: 创建用户
    - GET /users/{user_id}: 用户详情
    - PUT /users/{user_id}: 更新用户
    - DELETE /users/{user_id}: 删除用户
    - PUT /users/{user_id}/status: 启用/禁用用户
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, get_user_permissions
from app.api.deps import get_db
from app.core.security import hash_password
from app.state.models import RoleModel, UserModel, UserRoleModel

router = APIRouter(tags=["users"])


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    nickname: str | None = None
    email: str | None = None
    role_ids: list[int] = []
    data_scope: str = "self"


class UserUpdateRequest(BaseModel):
    nickname: str | None = None
    email: str | None = None
    status: str | None = None
    data_scope: str | None = None
    role_ids: list[int] | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    nickname: str | None
    email: str | None
    status: str
    data_scope: str
    roles: list[dict]
    last_login_at: str | None
    created_at: str

    class Config:
        from_attributes = True


def check_manage_permission(current_user: UserModel, db: Session):
    """检查当前用户是否有管理权限。"""
    perms = get_user_permissions(db, current_user.id)
    if "user:manage" not in perms:
        raise HTTPException(status_code=403, detail="Permission denied")


@router.get("", response_model=list[UserResponse])
async def list_users(
    keyword: str | None = None,
    status: str | None = None,
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
        result.append(
            {
                "id": u.id,
                "username": u.username,
                "nickname": u.nickname,
                "email": u.email,
                "status": u.status,
                "data_scope": u.data_scope,
                "roles": [
                    {"id": r.id, "name": r.name, "display_name": r.display_name} for r in roles
                ],
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                "created_at": u.created_at.isoformat(),
            }
        )
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

    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "status": user.status,
        "data_scope": user.data_scope,
        "roles": [],
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat(),
    }


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
