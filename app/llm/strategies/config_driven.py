from typing import Any, Dict, Optional

import yaml

from app.llm.client import LLMClient
from app.llm.strategies.base import RoutingStrategy
from app.config import get_settings


class ConfigDrivenStrategy(RoutingStrategy):
    name = "config_driven"

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/llm-routing.yaml"
        self._rules: Dict[str, Dict[str, str]] = {}
        self._load_config()

    def _load_config(self) -> None:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            self._rules = config.get("rules", {})
        except Exception:
            self._rules = {}

    def select_client(
        self,
        clients: Dict[str, LLMClient],
        task_type: str,
        context: Dict[str, Any],
    ) -> LLMClient:
        rule = self._rules.get(task_type)
        if rule:
            provider = rule.get("provider")
            if provider and provider in clients:
                return clients[provider]

        settings = get_settings()
        provider = settings.default_llm_provider
        if provider in clients:
            return clients[provider]

        if clients:
            return next(iter(clients.values()))

        raise RuntimeError("No LLM client available")
