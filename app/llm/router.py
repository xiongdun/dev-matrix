"""LLM 路由模块。

提供 LLMRouter 类，根据配置策略在多个 LLM 提供商之间进行路由选择。
支持 OpenAI 和 Anthropic 提供商，以及 quality_first、cost_first 等策略。

主要类：
    - LLMRouter: LLM 路由类，管理多个客户端并根据策略选择。

使用示例：
    ```python
    from app.llm.router import LLMRouter

    router = LLMRouter()
    result = await router.complete("Hello, world!")
    ```
"""

import logging
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.llm.client import LLMClient, OpenAIClient, AnthropicClient

logger = logging.getLogger(__name__)


class LLMRouter:
    """LLM 路由类，管理多个 LLM 客户端并根据策略选择。

    支持根据 quality_first、cost_first 或显式提供商策略选择客户端。

    Attributes:
        provider: 当前提供商名称。
        model: 当前模型名称。
        strategy: 选择策略。
        _clients: 已初始化的客户端字典。

    Example:
        ```python
        router = LLMRouter(provider="openai", model="gpt-4")
        response = await router.complete("Prompt text")
        ```
    """

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """初始化 LLM 路由。

        根据配置初始化可用的 LLM 客户端。

        Args:
            provider: 显式指定提供商，默认使用配置中的 default_llm_provider。
            model: 显式指定模型，默认使用配置中的 default_llm_model。
        """
        settings = get_settings()
        self.provider = provider or settings.default_llm_provider
        self.model = model or settings.default_llm_model
        self.strategy = settings.llm_strategy
        self._clients: Dict[str, LLMClient] = {}
        self._init_clients()

    def _init_clients(self):
        """初始化所有配置了 API 密钥的 LLM 客户端。"""
        settings = get_settings()
        if settings.openai_api_key:
            self._clients["openai"] = OpenAIClient(
                api_key=settings.openai_api_key,
                model=self.model if self.provider == "openai" else "gpt-4",
            )
            logger.debug("Initialized OpenAI client")
        if settings.anthropic_api_key:
            self._clients["anthropic"] = AnthropicClient(
                api_key=settings.anthropic_api_key,
                model=self.model if self.provider == "anthropic" else "claude-3-opus-20240229",
            )
            logger.debug("Initialized Anthropic client")
        if not self._clients:
            logger.warning("No LLM clients initialized: missing API keys")

    def _select_client(self) -> LLMClient:
        """根据策略选择 LLM 客户端。

        quality_first 优先选择 Anthropic，fallback 到 OpenAI；
        cost_first 优先选择 OpenAI，fallback 到 Anthropic；
        其他策略按显式 provider 选择。

        Returns:
            LLMClient: 选中的客户端。

        Raises:
            RuntimeError: 没有可用客户端时抛出。
        """
        if self.strategy == "quality_first":
            if "anthropic" in self._clients:
                logger.debug("Selected Anthropic client (quality_first)")
                return self._clients["anthropic"]
            if "openai" in self._clients:
                logger.debug("Selected OpenAI client (quality_first fallback)")
                return self._clients["openai"]
        elif self.strategy == "cost_first":
            if "openai" in self._clients:
                logger.debug("Selected OpenAI client (cost_first)")
                return self._clients["openai"]
            if "anthropic" in self._clients:
                logger.debug("Selected Anthropic client (cost_first fallback)")
                return self._clients["anthropic"]
        else:
            if self.provider in self._clients:
                logger.debug("Selected %s client (explicit provider)", self.provider)
                return self._clients[self.provider]

        available = list(self._clients.keys())
        logger.error(
            "No LLM client available for provider=%s, strategy=%s. Available clients: %s",
            self.provider,
            self.strategy,
            available,
        )
        raise RuntimeError(
            f"No LLM client available for provider='{self.provider}', strategy='{self.strategy}'. "
            f"Available clients: {available or 'none'}. "
            f"Please check that the corresponding API key is configured."
        )

    async def complete(self, prompt: str, **kwargs) -> str:
        """使用选中的客户端完成单轮文本生成。

        Args:
            prompt: 输入提示词。
            **kwargs: 额外参数，传递给客户端。

        Returns:
            str: 生成的文本。

        Raises:
            Exception: 调用失败时抛出。
        """
        client = self._select_client()
        logger.info("LLM complete via %s, prompt_length=%d", client.name, len(prompt))
        try:
            result = await client.complete(prompt, **kwargs)
            logger.info("LLM complete success via %s, result_length=%d", client.name, len(result))
            return result
        except Exception as exc:
            logger.error("LLM complete failed via %s: %s", client.name, exc)
            raise

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """使用选中的客户端进行多轮对话。

        Args:
            messages: 消息列表，每条消息包含 role 和 content。
            **kwargs: 额外参数，传递给客户端。

        Returns:
            str: 生成的回复文本。

        Raises:
            Exception: 调用失败时抛出。
        """
        client = self._select_client()
        logger.info("LLM chat via %s, messages=%d", client.name, len(messages))
        try:
            result = await client.chat(messages, **kwargs)
            logger.info("LLM chat success via %s, result_length=%d", client.name, len(result))
            return result
        except Exception as exc:
            logger.error("LLM chat failed via %s: %s", client.name, exc)
            raise
