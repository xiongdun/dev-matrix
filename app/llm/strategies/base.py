from abc import ABC, abstractmethod
from typing import Any

from app.llm.client import LLMClient


class RoutingStrategy(ABC):
    name: str = "base"

    @abstractmethod
    def select_client(
        self,
        clients: dict[str, LLMClient],
        task_type: str,
        context: dict[str, Any],
    ) -> LLMClient:
        pass
