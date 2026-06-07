"""Direct LLM 适配器。

直接调用 LLM API，不使用 Agent 框架。最轻量的方式。
"""

import logging
from collections.abc import AsyncIterator

from app.sdk.base import BaseSDK, SDKMessage, SDKRegistry, SDKResponse

logger = logging.getLogger(__name__)


@SDKRegistry.register("direct_llm")
class DirectLLMSDK(BaseSDK):
    """直接 LLM 调用适配器。"""

    name = "direct_llm"
    display_name = "Direct LLM"
    description = "直接调用 LLM API，不使用 Agent 框架，最轻量"

    async def chat(
        self,
        message: str,
        system_prompt: str,
        history: list[dict[str, str]] | None = None,
        **kwargs,
    ) -> SDKResponse:
        """直接调用 LLM API。"""
        try:
            from app.llm.router import LLMRouter

            router = LLMRouter()
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            if history:
                for h in history[-10:]:
                    messages.append({"role": h["role"], "content": h["content"]})

            messages.append({"role": "user", "content": message})

            response = await router.chat(messages)

            return SDKResponse(
                content=response,
                metadata={"sdk": self.name},
            )
        except Exception as e:
            logger.exception("Direct LLM error")
            return SDKResponse(content="", success=False, error=str(e))

    async def chat_stream(
        self,
        message: str,
        system_prompt: str,
        history: list[dict[str, str]] | None = None,
        **kwargs,
    ) -> AsyncIterator[SDKMessage]:
        """直接 LLM 流式输出。"""
        # 先用非流式，后续可以改为流式
        response = await self.chat(message, system_prompt, history, **kwargs)

        if response.content:
            yield SDKMessage(type="text", content=response.content)

        if response.error:
            yield SDKMessage(type="error", content=response.error)

        yield SDKMessage(type="done", content="")
