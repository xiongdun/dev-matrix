"""MCP 集成 API 模块。"""

import logging
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.mcp.manager import MCPServer, MCPServerStatus, mcp_manager, register_mcp_from_workspace
from app.state.models import UserModel

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/servers")
async def list_servers(
    current_user: UserModel = Depends(get_current_user),
):
    """获取所有 MCP 服务器。"""
    return {"servers": mcp_manager.get_stats()}


@router.get("/tools")
async def list_tools(
    current_user: UserModel = Depends(get_current_user),
):
    """获取所有可用的 MCP 工具。"""
    tools = mcp_manager.get_all_tools()
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "server": t.server_name,
            }
            for t in tools
        ]
    }


@router.post("/sync")
async def sync_from_workspace(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """从用户 workspace 同步 MCP 服务器配置。"""
    servers = register_mcp_from_workspace(user_id)
    return {
        "status": "ok",
        "synced": len(servers),
        "servers": [s.name for s in servers],
    }


@router.post("/health-check")
async def health_check(
    current_user: UserModel = Depends(get_current_user),
):
    """检查所有 MCP 服务器健康状态。"""
    results = await mcp_manager.health_check_all()
    return {"results": results}
