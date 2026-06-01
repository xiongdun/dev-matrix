"""角色管理 API 模块。

提供角色列表、创建、详情、更新、删除等管理接口，支持菜单和 Agent 权限分配。

主要路由：
    - GET /roles: 角色列表
    - POST /roles: 创建角色
    - GET /roles/{role_id}: 角色详情
    - PUT /roles/{role_id}: 更新角色
    - DELETE /roles/{role_id}: 删除角色
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, get_user_permissions
from app.api.deps import get_db
from app.state.models import MenuModel, RoleAgentModel, RoleMenuModel, RoleModel, UserModel

router = APIRouter(tags=["roles"])


class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    data_scope: str = "self"
    menu_ids: list[int] = []
    agent_names: list[str] = []


class RoleUpdateRequest(BaseModel):
    display_name: str | None = None
    description: str | None = None
    data_scope: str | None = None
    status: str | None = None
    menu_ids: list[int] | None = None
    agent_names: list[str] | None = None


class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str | None
    data_scope: str
    is_system: int
    status: str
    menus: list[dict]
    agents: list[str]

    class Config:
        from_attributes = True


def check_role_permission(current_user: UserModel, db: Session):
    """检查当前用户是否有角色管理权限。"""
    perms = get_user_permissions(db, current_user.id)
    if "role:manage" not in perms:
        raise HTTPException(status_code=403, detail="Permission denied")


@router.get("", response_model=list[RoleResponse])
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
        result.append(
            {
                "id": r.id,
                "name": r.name,
                "display_name": r.display_name,
                "description": r.description,
                "data_scope": r.data_scope,
                "is_system": r.is_system,
                "status": r.status,
                "menus": [{"id": m.id, "name": m.name, "title": m.title} for m in menus],
                "agents": [a[0] for a in agents],
            }
        )
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

    return {
        "id": role.id,
        "name": role.name,
        "display_name": role.display_name,
        "description": role.description,
        "data_scope": role.data_scope,
        "is_system": role.is_system,
        "status": role.status,
        "menus": [],
        "agents": [],
    }


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
