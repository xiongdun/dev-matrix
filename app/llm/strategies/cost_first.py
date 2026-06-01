from typing import Any

from app.llm.client import LLMClient
from app.llm.strategies.base import RoutingStrategy


class CostFirstStrategy(RoutingStrategy):
    name = "cost_first"

    PRIORITY = ["openai", "anthropic"]

    def select_client(
        self,
        clients: dict[str, LLMClient],
        task_type: str,
        context: dict[str, Any],
    ) -> LLMClient:
        for provider in self.PRIORITY:
            if provider in clients:
                return clients[provider]
        raise RuntimeError("No LLM client available")
