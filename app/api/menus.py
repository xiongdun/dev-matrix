"""菜单管理 API 模块。

提供菜单树、创建、详情、更新、删除等管理接口，支持动态菜单获取。

主要路由：
    - GET /menus: 菜单列表（树形）
    - GET /menus/tree: 完整菜单树（管理用）
    - GET /menus/my: 当前用户有权限的菜单树
    - POST /menus: 创建菜单
    - GET /menus/{menu_id}: 菜单详情
    - PUT /menus/{menu_id}: 更新菜单
    - DELETE /menus/{menu_id}: 删除菜单
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_user_permissions
from app.api.deps import get_current_user, get_db
from app.state.models import MenuModel, RoleMenuModel, UserModel

router = APIRouter(tags=["menus"])


class MenuCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=50)
    path: str | None = None
    icon: str | None = None
    parent_id: int | None = None
    sort_order: int = 0
    menu_type: str = "page"
    permission: str | None = None
    component: str | None = None
    is_visible: int = 1


class MenuUpdateRequest(BaseModel):
    title: str | None = None
    path: str | None = None
    icon: str | None = None
    parent_id: int | None = None
    sort_order: int | None = None
    menu_type: str | None = None
    permission: str | None = None
    component: str | None = None
    is_visible: int | None = None
    status: str | None = None


class MenuResponse(BaseModel):
    id: int
    name: str
    title: str
    path: str | None
    icon: str | None
    parent_id: int | None
    sort_order: int
    menu_type: str
    permission: str | None
    component: str | None
    is_visible: int
    status: str
    children: list["MenuResponse"] = []

    class Config:
        from_attributes = True


def check_menu_permission(current_user: UserModel, db: Session):
    """检查当前用户是否有菜单管理权限。"""
    perms = get_user_permissions(db, current_user.id)
    if "menu:manage" not in perms:
        raise HTTPException(status_code=403, detail="Permission denied")


def build_menu_tree(menus: list[MenuModel], parent_id: int | None = None) -> list[dict]:
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

    role_ids = (
        db.query(UserRoleModel.role_id).filter(UserRoleModel.user_id == current_user.id).all()
    )
    role_ids = [r[0] for r in role_ids]

    if not role_ids:
        return []

    menu_ids = (
        db.query(RoleMenuModel.menu_id).filter(RoleMenuModel.role_id.in_(role_ids)).distinct().all()
    )
    menu_ids = [m[0] for m in menu_ids]

    if not menu_ids:
        return []

    menus = (
        db.query(MenuModel)
        .filter(
            MenuModel.id.in_(menu_ids),
            MenuModel.status == "active",
            MenuModel.is_visible == 1,
        )
        .all()
    )

    return build_menu_tree(menus)


@router.get("", response_model=list[MenuResponse])
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
