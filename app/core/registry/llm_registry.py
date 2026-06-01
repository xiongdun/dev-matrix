from app.core.registry.base import Registry
from app.llm.client import LLMClient

llm_registry: Registry[LLMClient] = Registry()


def register_llm_provider(name: str | None = None):
    def decorator(cls: type[LLMClient]) -> type[LLMClient]:
        llm_registry.register(name or cls.__name__, cls)
        return cls

    return decorator


# noqa: E402
from app.llm.client import AnthropicClient, OpenAIClient  # noqa: E402

llm_registry.register("openai", OpenAIClient)
llm_registry.register("anthropic", AnthropicClient)
