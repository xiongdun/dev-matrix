from typing import Any, Dict

from app.llm.client import LLMClient
from app.llm.strategies.base import RoutingStrategy


class CostFirstStrategy(RoutingStrategy):
    name = "cost_first"

    PRIORITY = ["openai", "anthropic"]

    def select_client(
        self,
        clients: Dict[str, LLMClient],
        task_type: str,
        context: Dict[str, Any],
    ) -> LLMClient:
        for provider in self.PRIORITY:
            if provider in clients:
                return clients[provider]
        raise RuntimeError("No LLM client available")
