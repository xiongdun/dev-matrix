from abc import ABC, abstractmethod
from typing import Any, Dict


class PromptTemplate(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def render(self, context: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def validate_context(self, context: Dict[str, Any]) -> bool:
        pass


class Jinja2PromptTemplate(PromptTemplate):
    def __init__(self, name: str, source: str, description: str = ""):
        self.name = name
        self._source = source
        self.description = description
        self._template = None
        self._compile()

    def _compile(self) -> None:
        try:
            from jinja2 import Template
            self._template = Template(self._source)
        except ImportError:
            raise RuntimeError("jinja2 not installed. Install with: pip install jinja2")

    def render(self, context: Dict[str, Any]) -> str:
        if self._template is None:
            raise RuntimeError("Template not compiled")
        return self._template.render(**context)

    def validate_context(self, context: Dict[str, Any]) -> bool:
        try:
            self.render(context)
            return True
        except Exception:
            return False
