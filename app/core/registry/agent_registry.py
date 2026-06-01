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

from app.agents.base import BaseAgent
from app.core.registry.base import Registry

# 全局 Agent 注册表实例
agent_registry: Registry[BaseAgent] = Registry()


def register_agent(name: str | None = None):
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

    def decorator(cls: type[BaseAgent]) -> type[BaseAgent]:
        agent_registry.register(name or cls.__name__, cls)
        return cls

    return decorator


# 延迟注册内置 Agent，避免循环导入
def _register_builtin_agents() -> None:
    """注册所有内置 Agent。在应用启动时调用。"""
    from app.agents.architect import ArchitectAgent
    from app.agents.business_analyst import BusinessAnalystAgent
    from app.agents.code_reviewer import CodeReviewerAgent
    from app.agents.developer import DeveloperAgent
    from app.agents.product_manager import ProductManagerAgent
    from app.agents.project_manager import ProjectManagerAgent
    from app.agents.qa import QAAgent

    agent_registry.register("business_analyst", BusinessAnalystAgent)
    agent_registry.register("product_manager", ProductManagerAgent)
    agent_registry.register("architect", ArchitectAgent)
    agent_registry.register("developer", DeveloperAgent)
    agent_registry.register("qa", QAAgent)
    agent_registry.register("project_manager", ProjectManagerAgent)
    agent_registry.register("code_reviewer", CodeReviewerAgent)


# 应用启动时自动注册（如果导入链已完整）
try:
    _register_builtin_agents()
except ImportError:
    pass  # 循环导入时跳过，由调用方在适当时机注册
