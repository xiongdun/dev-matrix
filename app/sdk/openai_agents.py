"""OpenAI 兼容 SDK 适配器。

使用 openai 库直接调用 Chat Completions API，
支持小米等 OpenAI 兼容 API（不需要 Responses API）。
"""

import logging
from collections.abc import AsyncIterator

from app.sdk.base import BaseSDK, SDKMessage, SDKRegistry, SDKResponse

logger = logging.getLogger(__name__)


@SDKRegistry.register("openai_agents")
class OpenAIAgentsSDK(BaseSDK):
    """OpenAI 兼容 SDK 适配器（使用 Chat Completions API）。"""

    name = "openai_agents"
    display_name = "OpenAI Agents"
    description = "基于 OpenAI Chat Completions API，支持 tool calling 和多轮对话"

    def __init__(
        self,
        model: str = "mimo-v2.5-pro",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def is_available(self) -> bool:
        try:
            import openai  # noqa: F401
            return bool(self.api_key)
        except ImportError:
            return False

    async def chat(
        self,
        message: str,
        system_prompt: str,
        history: list[dict[str, str]] | None = None,
        **kwargs,
    ) -> SDKResponse:
        """使用 OpenAI Chat Completions API 发送消息。"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if history:
                for h in history[-10:]:
                    messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": message})

            # 调用 API
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4096,
            )

            ai_content = response.choices[0].message.content or ""

            return SDKResponse(
                content=ai_content,
                metadata={"sdk": self.name, "model": self.model},
            )
        except Exception as e:
            logger.exception("OpenAI SDK error")
            return SDKResponse(content="", success=False, error=str(e))

    async def chat_stream(
        self,
        message: str,
        system_prompt: str,
        history: list[dict[str, str]] | None = None,
        **kwargs,
    ) -> AsyncIterator[SDKMessage]:
        """流式输出。"""
        response = await self.chat(message, system_prompt, history, **kwargs)

        if response.content:
            yield SDKMessage(type="text", content=response.content)
        if response.error:
            yield SDKMessage(type="error", content=response.error)
        yield SDKMessage(type="done", content="")
