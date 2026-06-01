from typing import Any

from app.core.registry.base import Registry
from app.prompts.engine import Jinja2PromptTemplate, PromptTemplate


class PromptRegistry:
    def __init__(self):
        self._registry: Registry[PromptTemplate] = Registry()
        self._metadata: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        template: PromptTemplate,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._registry.register(name, template.__class__)
        self._metadata[name] = metadata or {}

    def get(self, name: str) -> type[PromptTemplate]:
        return self._registry.get(name)

    def create(self, name: str, source: str, description: str = "") -> Jinja2PromptTemplate:
        template = Jinja2PromptTemplate(name=name, source=source, description=description)
        self.register(name, template, {"description": description})
        return template

    def list(self) -> dict[str, type[PromptTemplate]]:
        return self._registry.list()

    def get_metadata(self, name: str) -> dict[str, Any]:
        return self._metadata.get(name, {}).copy()

    def exists(self, name: str) -> bool:
        return self._registry.exists(name)

    def unregister(self, name: str) -> None:
        self._registry.unregister(name)
        if name in self._metadata:
            del self._metadata[name]
