from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.llm.client import LLMClient, OpenAIClient, AnthropicClient


class LLMRouter:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        settings = get_settings()
        self.provider = provider or settings.default_llm_provider
        self.model = model or settings.default_llm_model
        self.strategy = settings.llm_strategy
        self._clients: Dict[str, LLMClient] = {}
        self._init_clients()

    def _init_clients(self):
        settings = get_settings()
        if settings.openai_api_key:
            self._clients["openai"] = OpenAIClient(
                api_key=settings.openai_api_key,
                model=self.model if self.provider == "openai" else "gpt-4",
            )
        if settings.anthropic_api_key:
            self._clients["anthropic"] = AnthropicClient(
                api_key=settings.anthropic_api_key,
                model=self.model if self.provider == "anthropic" else "claude-3-opus-20240229",
            )

    def _select_client(self) -> LLMClient:
        if self.strategy == "quality_first":
            if "anthropic" in self._clients:
                return self._clients["anthropic"]
            if "openai" in self._clients:
                return self._clients["openai"]
        elif self.strategy == "cost_first":
            if "openai" in self._clients:
                return self._clients["openai"]
            if "anthropic" in self._clients:
                return self._clients["anthropic"]
        else:
            if self.provider in self._clients:
                return self._clients[self.provider]
        raise RuntimeError(f"No LLM client available for provider={self.provider}")

    async def complete(self, prompt: str, **kwargs) -> str:
        client = self._select_client()
        return await client.complete(prompt, **kwargs)

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        client = self._select_client()
        return await client.chat(messages, **kwargs)
