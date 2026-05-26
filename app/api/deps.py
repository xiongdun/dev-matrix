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
