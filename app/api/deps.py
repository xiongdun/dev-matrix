"""API 依赖模块。

提供 FastAPI 路由使用的依赖注入函数。
"""

from app.state.models import get_db

__all__ = ["get_db"]
