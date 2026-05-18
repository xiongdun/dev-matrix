from typing import Type, Optional

from app.core.registry.base import Registry
from app.llm.client import LLMClient

llm_registry: Registry[LLMClient] = Registry()


def register_llm_provider(name: Optional[str] = None):
    def decorator(cls: Type[LLMClient]) -> Type[LLMClient]:
        llm_registry.register(name or cls.__name__, cls)
        return cls

    return decorator


# noqa: E402
from app.llm.client import OpenAIClient, AnthropicClient  # noqa: E402

llm_registry.register("openai", OpenAIClient)
llm_registry.register("anthropic", AnthropicClient)
