from typing import Type

from app.core.registry.base import Registry
from app.llm.client import LLMClient

llm_registry: Registry[LLMClient] = Registry()


def register_llm_provider(name: str = None):
    def decorator(cls: Type[LLMClient]) -> Type[LLMClient]:
        llm_registry.register(name or cls.__name__, cls)
        return cls
    return decorator


from app.llm.client import OpenAIClient, AnthropicClient

llm_registry.register("openai", OpenAIClient)
llm_registry.register("anthropic", AnthropicClient)
