from abc import ABC, abstractmethod
from typing import Any, Dict

from app.llm.client import LLMClient


class RoutingStrategy(ABC):
    name: str = "base"

    @abstractmethod
    def select_client(
        self,
        clients: Dict[str, LLMClient],
        task_type: str,
        context: Dict[str, Any],
    ) -> LLMClient:
        pass
