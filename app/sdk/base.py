"""SDK 抽象接口模块。

定义所有 Agent SDK 的统一接口，支持多种后端（Claude Code、OpenAI Agents 等）。
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SDKMessage:
    """SDK 消息基类。"""
    type: str  # "text" | "tool_call" | "tool_result" | "error" | "done"
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SDKResponse:
    """SDK 完整响应。"""
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None


class BaseSDK(ABC):
    """Agent SDK 抽象基类。"""

    name: str = "base"
    display_name: str = "Base SDK"
    description: str = ""

    @abstractmethod
    async def chat(
        self,
        message: str,
        system_prompt: str,
        history: list[dict[str, str]] | None = None,
        **kwargs,
    ) -> SDKResponse:
        """发送消息并获取完整回复。

        Args:
            message: 用户消息
            system_prompt: 系统提示词
            history: 历史消息列表 [{"role": "user/assistant", "content": "..."}]
            **kwargs: SDK 特定参数

        Returns:
            SDKResponse: 包含回复内容和工具调用记录
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        message: str,
        system_prompt: str,
        history: list[dict[str, str]] | None = None,
        **kwargs,
    ) -> AsyncIterator[SDKMessage]:
        """流式发送消息，逐块返回。

        Args:
            message: 用户消息
            system_prompt: 系统提示词
            history: 历史消息列表
            **kwargs: SDK 特定参数

        Yields:
            SDKMessage: 流式消息块
        """
        pass

    def is_available(self) -> bool:
        """检查 SDK 是否可用。"""
        return True

    def get_config(self) -> dict[str, Any]:
        """获取当前 SDK 配置。"""
        return {"name": self.name, "display_name": self.display_name}


class SDKRegistry:
    """SDK 注册表。"""

    _sdks: dict[str, type[BaseSDK]] = {}

    @classmethod
    def register(cls, name: str):
        """装饰器：注册 SDK 类。"""
        def decorator(sdk_cls: type[BaseSDK]) -> type[BaseSDK]:
            cls._sdks[name] = sdk_cls
            return sdk_cls
        return decorator

    @classmethod
    def get(cls, name: str) -> type[BaseSDK] | None:
        return cls._sdks.get(name)

    @classmethod
    def list_all(cls) -> dict[str, type[BaseSDK]]:
        return dict(cls._sdks)

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseSDK:
        sdk_cls = cls._sdks.get(name)
        if sdk_cls is None:
            raise ValueError(f"Unknown SDK: {name}. Available: {list(cls._sdks.keys())}")
        return sdk_cls(**kwargs)
