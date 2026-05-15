"""Agent 注册表模块。

提供全局 Agent 注册表实例和注册装饰器。

主要对象：
    - agent_registry: 全局 Agent 注册表实例。
    - register_agent: Agent 注册装饰器。

使用示例：
    ```python
    from app.core.registry.agent_registry import register_agent

    @register_agent()
    class MyAgent(BaseAgent):
        name = "my_agent"
    ```
"""

from typing import Type

from app.core.registry.base import Registry
from app.agents.base import BaseAgent

# 全局 Agent 注册表实例
agent_registry: Registry[BaseAgent] = Registry()


def register_agent(name: str = None):
    """Agent 注册装饰器。

    将 Agent 类注册到全局 Agent 注册表。

    Args:
        name: 自定义注册名称，默认使用类的 __name__。

    Returns:
        Callable: 装饰器函数。

    Example:
        ```python
        @register_agent("custom_name")
        class MyAgent(BaseAgent):
            name = "my_agent"
        ```
    """
    def decorator(cls: Type[BaseAgent]) -> Type[BaseAgent]:
        agent_registry.register(name or cls.__name__, cls)
        return cls
    return decorator


# 导入并注册所有内置 Agent
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
