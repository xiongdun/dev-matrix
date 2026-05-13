from typing import Type

from app.core.registry.base import Registry
from app.agents.base import BaseAgent

agent_registry: Registry[BaseAgent] = Registry()


def register_agent(name: str = None):
    def decorator(cls: Type[BaseAgent]) -> Type[BaseAgent]:
        agent_registry.register(name or cls.__name__, cls)
        return cls
    return decorator


from app.agents.business_analyst import BusinessAnalystAgent
from app.agents.product_manager import ProductManagerAgent
from app.agents.architect import ArchitectAgent
from app.agents.developer import DeveloperAgent
from app.agents.qa import QAAgent

agent_registry.register("business_analyst", BusinessAnalystAgent)
agent_registry.register("product_manager", ProductManagerAgent)
agent_registry.register("architect", ArchitectAgent)
agent_registry.register("developer", DeveloperAgent)
agent_registry.register("qa", QAAgent)
