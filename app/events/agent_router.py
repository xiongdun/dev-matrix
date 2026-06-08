"""Agent 事件路由模块。

将事件路由到对应的 Agent，支持：
- Agent 能力声明
- 事件→Agent 自动匹配
- Agent 事件处理器注册
"""

import logging
from typing import Any

from app.events.enhanced_bus import EnhancedEvent, enhanced_bus

logger = logging.getLogger(__name__)


class AgentEventRouter:
    """Agent 事件路由器。

    管理 Agent 的事件订阅和路由。
    """

    def __init__(self):
        # agent_role -> 事件类型列表
        self._agent_subscriptions: dict[str, list[str]] = {}
        # agent_role -> 事件处理器
        self._agent_handlers: dict[str, Any] = {}

    def register_agent(
        self,
        agent_role: str,
        event_types: list[str],
        handler: Any = None,
    ) -> None:
        """注册 Agent 的事件订阅。

        Args:
            agent_role: Agent 角色名
            event_types: 订阅的事件类型列表
            handler: 事件处理器（可选，默认使用 Agent 的 generate_proposal）
        """
        self._agent_subscriptions[agent_role] = event_types
        if handler:
            self._agent_handlers[agent_role] = handler

        # 注册到事件总线
        for event_type in event_types:
            enhanced_bus.subscribe(
                event_type=event_type,
                handler=lambda e, role=agent_role: self._route_to_agent(role, e),
            )

        logger.info("Agent '%s' registered for events: %s", agent_role, event_types)

    async def _route_to_agent(self, agent_role: str, event: EnhancedEvent) -> None:
        """将事件路由到指定 Agent。"""
        logger.info("Routing event '%s' to agent '%s'", event.type, agent_role)

        # 如果事件指定了目标 Agent，检查是否匹配
        if event.target_agents and agent_role not in event.target_agents:
            return

        # 调用 Agent 处理器
        handler = self._agent_handlers.get(agent_role)
        if handler:
            try:
                await handler(event)
            except Exception:
                logger.exception("Agent '%s' failed to handle event '%s'", agent_role, event.type)

    def get_agent_events(self, agent_role: str) -> list[str]:
        """获取 Agent 订阅的事件类型。"""
        return self._agent_subscriptions.get(agent_role, [])

    def get_all_subscriptions(self) -> dict[str, list[str]]:
        """获取所有 Agent 的事件订阅。"""
        return dict(self._agent_subscriptions)


# 全局 Agent 事件路由器
agent_router = AgentEventRouter()


# 预定义 Agent 事件订阅
DEFAULT_AGENT_EVENTS = {
    "business_analyst": [
        "github.push",
        "github.pull_request",
        "requirement.created",
        "requirement.updated",
    ],
    "architect": [
        "requirement.approved",
        "github.push",
    ],
    "developer": [
        "architecture.approved",
        "github.issue",
    ],
    "qa": [
        "code.generated",
        "github.pull_request",
    ],
    "code_reviewer": [
        "github.pull_request",
        "code.generated",
    ],
    "project_manager": [
        "workflow.started",
        "workflow.completed",
        "workflow.failed",
        "approval.required",
    ],
}


def register_default_agent_events() -> None:
    """注册默认的 Agent 事件订阅。"""
    for agent_role, events in DEFAULT_AGENT_EVENTS.items():
        agent_router.register_agent(agent_role, events)
    logger.info("Registered default agent events for %d agents", len(DEFAULT_AGENT_EVENTS))
