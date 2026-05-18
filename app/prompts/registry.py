from typing import Any, Dict, Optional, Type

from app.core.registry.base import Registry
from app.prompts.engine import Jinja2PromptTemplate, PromptTemplate


class PromptRegistry:
    def __init__(self):
        self._registry: Registry[PromptTemplate] = Registry()
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        template: PromptTemplate,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._registry.register(name, template.__class__)
        self._metadata[name] = metadata or {}

    def get(self, name: str) -> Type[PromptTemplate]:
        return self._registry.get(name)

    def create(
        self, name: str, source: str, description: str = ""
    ) -> Jinja2PromptTemplate:
        template = Jinja2PromptTemplate(
            name=name, source=source, description=description
        )
        self.register(name, template, {"description": description})
        return template

    def list(self) -> Dict[str, Type[PromptTemplate]]:
        return self._registry.list()

    def get_metadata(self, name: str) -> Dict[str, Any]:
        return self._metadata.get(name, {}).copy()

    def exists(self, name: str) -> bool:
        return self._registry.exists(name)

    def unregister(self, name: str) -> None:
        self._registry.unregister(name)
        if name in self._metadata:
            del self._metadata[name]
