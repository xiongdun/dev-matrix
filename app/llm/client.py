"""LLM 客户端模块。

提供 LLMClient 抽象基类及 OpenAIClient、AnthropicClient 实现。
支持 complete 和 chat 两种调用模式，并集成重试机制。

主要类：
    - LLMClient: LLM 客户端抽象基类。
    - OpenAIClient: OpenAI API 客户端。
    - AnthropicClient: Anthropic API 客户端。

使用示例：
    ```python
    from app.llm.client import OpenAIClient

    client = OpenAIClient(api_key="sk-...", model="gpt-4")
    result = await client.complete("Hello!")
    ```
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings
from app.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """LLM 客户端抽象基类。

    所有 LLM 客户端必须继承此类并实现 complete 和 chat 方法。

    Attributes:
        name: 客户端名称标识。
    """

    name: str = "base"

    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """单轮文本生成。

        Args:
            prompt: 输入提示词。
            **kwargs: 额外参数。

        Returns:
            str: 生成的文本。
        """
        pass

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """多轮对话。

        Args:
            messages: 消息列表。
            **kwargs: 额外参数。

        Returns:
            str: 生成的回复文本。
        """
        pass


class OpenAIClient(LLMClient):
    """OpenAI API 客户端。

    支持 GPT 系列模型的 complete 和 chat 调用。

    Attributes:
        name: 客户端名称，固定为 "openai"。

    Example:
        ```python
        client = OpenAIClient(api_key="sk-...", model="gpt-4")
        result = await client.chat([{"role": "user", "content": "Hello"}])
        ```
    """

    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """初始化 OpenAI 客户端。

        Args:
            api_key: OpenAI API 密钥，默认从配置读取。
            model: 模型名称。
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    async def complete(self, prompt: str, **kwargs) -> str:
        """单轮文本生成，内部转换为 chat 格式调用。

        Args:
            prompt: 输入提示词。
            **kwargs: 额外参数。

        Returns:
            str: 生成的文本。
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, **kwargs)

    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError),
    )
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """多轮对话。

        使用 httpx 异步调用 OpenAI Chat Completions API，
        集成指数退避重试机制。

        Args:
            messages: 消息列表，每条包含 role 和 content。
            **kwargs: 额外参数，可覆盖 model、temperature、max_tokens。

        Returns:
            str: 生成的回复文本。

        Raises:
            httpx.HTTPStatusError: API 返回非 2xx 状态码。
            httpx.TimeoutException: 请求超时。
            httpx.ConnectError: 连接错误。
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        logger.debug(
            "OpenAI chat request: model=%s, messages=%d",
            payload["model"],
            len(messages),
        )
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60,
                )
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "OpenAI API error: status=%s, response=%s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.TimeoutException as exc:
            logger.error("OpenAI API timeout after 60s")
            raise
        except httpx.ConnectError as exc:
            logger.error("OpenAI API connection error: %s", exc)
            raise
        except httpx.NetworkError as exc:
            logger.error("OpenAI API network error: %s", exc)
            raise
        except Exception as exc:
            logger.exception("Unexpected error calling OpenAI API")
            raise

        # 解析响应
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        logger.debug(
            "OpenAI chat response: model=%s, usage=%s",
            data.get("model"),
            data.get("usage"),
        )
        return content


class AnthropicClient(LLMClient):
    """Anthropic API 客户端。

    支持 Claude 系列模型的 complete 和 chat 调用。

    Attributes:
        name: 客户端名称，固定为 "anthropic"。

    Example:
        ```python
        client = AnthropicClient(api_key="...", model="claude-3-opus")
        result = await client.chat([{"role": "user", "content": "Hello"}])
        ```
    """

    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        """初始化 Anthropic 客户端。

        Args:
            api_key: Anthropic API 密钥，默认从配置读取。
            model: 模型名称。
        """
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"

    async def complete(self, prompt: str, **kwargs) -> str:
        """单轮文本生成，内部转换为 chat 格式调用。

        Args:
            prompt: 输入提示词。
            **kwargs: 额外参数。

        Returns:
            str: 生成的文本。
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, **kwargs)

    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exceptions=(httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError),
    )
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """多轮对话。

        使用 httpx 异步调用 Anthropic Messages API，
        集成指数退避重试机制。

        Args:
            messages: 消息列表，每条包含 role 和 content。
            **kwargs: 额外参数，可覆盖 model、max_tokens、temperature。

        Returns:
            str: 生成的回复文本。

        Raises:
            httpx.HTTPStatusError: API 返回非 2xx 状态码。
            httpx.TimeoutException: 请求超时。
            httpx.ConnectError: 连接错误。
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.7),
        }
        logger.debug(
            "Anthropic chat request: model=%s, messages=%d",
            payload["model"],
            len(messages),
        )
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                    timeout=60,
                )
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Anthropic API error: status=%s, response=%s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
        except httpx.TimeoutException as exc:
            logger.error("Anthropic API timeout after 60s")
            raise
        except httpx.ConnectError as exc:
            logger.error("Anthropic API connection error: %s", exc)
            raise
        except httpx.NetworkError as exc:
            logger.error("Anthropic API network error: %s", exc)
            raise
        except Exception as exc:
            logger.exception("Unexpected error calling Anthropic API")
            raise

        # 解析响应
        data = resp.json()
        content = data["content"][0]["text"]
        logger.debug(
            "Anthropic chat response: model=%s, usage=%s",
            data.get("model"),
            data.get("usage"),
        )
        return content
