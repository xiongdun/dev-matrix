"""Agent 消息总线模块。

支持 Agent 间直接通信和共享上下文：
- Agent 消息发送/接收
- 共享上下文池
- 消息持久化
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """消息类型。"""
    REQUEST = "request"       # 请求：A 请求 B 执行某任务
    RESPONSE = "response"     # 响应：B 回复 A 的请求
    NOTIFICATION = "notification"  # 通知：A 通知 B 某事发生
    BROADCAST = "broadcast"   # 广播：A 通知所有 Agent


class MessageStatus(str, Enum):
    """消息状态。"""
    PENDING = "pending"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class AgentMessage:
    """Agent 消息。"""
    id: str = ""
    from_agent: str = ""
    to_agent: str = ""
    message_type: MessageType = MessageType.NOTIFICATION
    subject: str = ""
    content: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    status: MessageStatus = MessageStatus.PENDING
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reply_to: str | None = None  # 回复的消息 ID
    project_id: str | None = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


@dataclass
class SharedContext:
    """共享上下文。"""
    key: str
    value: Any
    updated_by: str = ""
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    project_id: str | None = None


class AgentMessageBus:
    """Agent 消息总线。

    支持：
    - Agent 间直接消息
    - 广播消息
    - 共享上下文池
    - 消息持久化到文件
    """

    def __init__(self, persist_dir: str | None = None):
        self._messages: list[AgentMessage] = []
        self._shared_context: dict[str, SharedContext] = {}
        self._agent_queues: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self._subscribers: dict[str, list] = defaultdict(list)
        self._persist_dir = persist_dir
        self._max_messages = 1000

    async def send(self, message: AgentMessage) -> str:
        """发送消息到指定 Agent。"""
        if not message.id:
            message.id = str(uuid.uuid4())[:8]

        self._messages.append(message)
        if len(self._messages) > self._max_messages:
            self._messages = self._messages[-self._max_messages:]

        # 放入目标 Agent 队列
        if message.message_type == MessageType.BROADCAST:
            for agent_role, queue in self._agent_queues.items():
                if agent_role != message.from_agent:
                    await queue.put(message)
        else:
            await self._agent_queues[message.to_agent].put(message)

        # 通知订阅者
        for sub in self._subscribers.get(message.to_agent, []):
            try:
                await sub(message)
            except Exception:
                logger.exception("Subscriber error for agent %s", message.to_agent)

        logger.info(
            "Message sent: %s -> %s [%s] %s",
            message.from_agent, message.to_agent,
            message.message_type.value, message.subject,
        )
        return message.id

    async def receive(
        self,
        agent_role: str,
        timeout: float = 30.0,
    ) -> AgentMessage | None:
        """从队列接收消息。"""
        try:
            return await asyncio.wait_for(
                self._agent_queues[agent_role].get(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            return None

    def subscribe(self, agent_role: str, handler) -> None:
        """订阅消息。"""
        self._subscribers[agent_role].append(handler)

    def get_messages(
        self,
        agent_role: str | None = None,
        project_id: str | None = None,
        limit: int = 50,
    ) -> list[AgentMessage]:
        """获取消息历史。"""
        msgs = self._messages
        if agent_role:
            msgs = [m for m in msgs if m.to_agent == agent_role or m.from_agent == agent_role]
        if project_id:
            msgs = [m for m in msgs if m.project_id == project_id]
        return msgs[-limit:]

    # ===== 共享上下文 =====

    def set_context(self, key: str, value: Any, updated_by: str, project_id: str | None = None) -> None:
        """设置共享上下文。"""
        self._shared_context[key] = SharedContext(
            key=key,
            value=value,
            updated_by=updated_by,
            project_id=project_id,
        )
        logger.info("Context set: %s by %s", key, updated_by)

    def get_context(self, key: str) -> Any | None:
        """获取共享上下文。"""
        ctx = self._shared_context.get(key)
        return ctx.value if ctx else None

    def get_all_context(self, project_id: str | None = None) -> dict[str, Any]:
        """获取所有共享上下文。"""
        result = {}
        for key, ctx in self._shared_context.items():
            if project_id is None or ctx.project_id == project_id:
                result[key] = ctx.value
        return result

    def delete_context(self, key: str) -> bool:
        """删除共享上下文。"""
        if key in self._shared_context:
            del self._shared_context[key]
            return True
        return False

    def get_stats(self) -> dict[str, Any]:
        """获取消息总线统计。"""
        return {
            "total_messages": len(self._messages),
            "shared_contexts": len(self._shared_context),
            "agent_queues": {k: v.qsize() for k, v in self._agent_queues.items()},
        }


# 全局实例
agent_bus = AgentMessageBus()
