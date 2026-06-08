"""MCP 集成增强模块。

支持：
- MCP 服务器发现和连接
- MCP 工具注册到 Agent
- MCP 服务器健康监控
- MCP 工具调用代理
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MCPServerStatus(str, Enum):
    """MCP 服务器状态。"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPTool:
    """MCP 工具定义。"""
    name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    server_name: str = ""


@dataclass
class MCPServer:
    """MCP 服务器。"""
    name: str
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str = ""  # HTTP/SSE 模式
    status: MCPServerStatus = MCPServerStatus.DISCONNECTED
    tools: list[MCPTool] = field(default_factory=list)
    last_health_check: datetime | None = None
    error_message: str = ""


class MCPManager:
    """MCP 服务器管理器。"""

    def __init__(self):
        self._servers: dict[str, MCPServer] = {}

    def register_server(self, server: MCPServer) -> None:
        """注册 MCP 服务器。"""
        self._servers[server.name] = server
        logger.info("MCP server registered: %s", server.name)

    def unregister_server(self, name: str) -> None:
        """注销 MCP 服务器。"""
        self._servers.pop(name, None)

    def get_server(self, name: str) -> MCPServer | None:
        return self._servers.get(name)

    def list_servers(self) -> list[MCPServer]:
        return list(self._servers.values())

    def get_all_tools(self) -> list[MCPTool]:
        """获取所有已注册的 MCP 工具。"""
        tools = []
        for server in self._servers.values():
            if server.status == MCPServerStatus.CONNECTED:
                tools.extend(server.tools)
        return tools

    def update_server_status(self, name: str, status: MCPServerStatus, error: str = "") -> None:
        """更新服务器状态。"""
        server = self._servers.get(name)
        if server:
            server.status = status
            server.error_message = error
            server.last_health_check = datetime.now(timezone.utc)

    async def health_check_all(self) -> dict[str, bool]:
        """检查所有服务器健康状态。"""
        results = {}
        for name, server in self._servers.items():
            try:
                # 简单的健康检查：检查服务器是否可达
                if server.url:
                    import httpx
                    async with httpx.AsyncClient(trust_env=False) as client:
                        resp = await client.get(f"{server.url}/health", timeout=5)
                        healthy = resp.status_code == 200
                else:
                    # stdio 模式：假设已连接即健康
                    healthy = server.status == MCPServerStatus.CONNECTED

                self.update_server_status(name, MCPServerStatus.CONNECTED if healthy else MCPServerStatus.ERROR)
                results[name] = healthy
            except Exception as e:
                self.update_server_status(name, MCPServerStatus.ERROR, str(e))
                results[name] = False

        return results

    def get_stats(self) -> dict[str, Any]:
        """获取 MCP 统计。"""
        return {
            "total_servers": len(self._servers),
            "connected": sum(1 for s in self._servers.values() if s.status == MCPServerStatus.CONNECTED),
            "total_tools": sum(len(s.tools) for s in self._servers.values()),
            "servers": {
                name: {
                    "status": s.status.value,
                    "tools_count": len(s.tools),
                    "error": s.error_message,
                }
                for name, s in self._servers.items()
            },
        }


# 全局 MCP 管理器
mcp_manager = MCPManager()


def register_mcp_from_workspace(user_id: int) -> list[MCPServer]:
    """从用户 workspace 注册 MCP 服务器。"""
    from app.memory.manager import get_user_mcp_servers

    servers = []
    mcp_configs = get_user_mcp_servers(user_id)

    for config in mcp_configs:
        server = MCPServer(
            name=config.get("name", ""),
            command=config.get("命令", ""),
            args=config.get("命令", "").split()[1:] if config.get("命令") else [],
        )

        # 注册工具
        for tool_info in config.get("tools", []):
            server.tools.append(MCPTool(
                name=tool_info.get("name", ""),
                description=tool_info.get("description", ""),
                server_name=server.name,
            ))

        mcp_manager.register_server(server)
        servers.append(server)

    return servers
