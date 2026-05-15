"""技能注册表模块。

提供 SkillRegistry 类用于管理技能的注册和发现，
以及 register_skill 装饰器用于便捷注册。

主要类/函数：
    - SkillRegistry: 技能注册表，继承自通用 Registry。
    - register_skill: 技能注册装饰器。
    - _global_registry: 全局技能注册表实例。

使用示例：
    ```python
    from app.skills.registry import register_skill
    from app.skills.base import BaseSkill

    @register_skill()
    class MySkill(BaseSkill):
        name = "my_skill"
        description = "A custom skill"

        async def execute(self, context):
            return SkillResult(output="done")
    ```
"""

from typing import Dict, Optional, Type

from app.core.registry.base import Registry
from app.skills.base import BaseSkill, SkillConfig


class SkillRegistry(Registry[BaseSkill]):
    """技能注册表，管理技能的注册、获取和发现。

    继承自通用 Registry，提供技能特有的创建和发现方法。

    Attributes:
        无公共属性，内部存储继承自 Registry。

    Example:
        ```python
        registry = SkillRegistry()
        registry.register("my_skill", MySkill)
        skill = registry.create("my_skill", config)
        ```
    """

    def create(self, name: str, config: Optional[SkillConfig] = None) -> BaseSkill:
        """创建技能实例。

        Args:
            name: 已注册的技能名称。
            config: 可选的技能配置。

        Returns:
            BaseSkill: 技能实例。

        Raises:
            KeyError: 技能未注册时抛出。
        """
        skill_class = self.get(name)
        return skill_class(config)

    def discover(self, package: str = "app.skills") -> Dict[str, Type[BaseSkill]]:
        """自动发现指定包中的技能类。

        Args:
            package: 要扫描的包名。

        Returns:
            Dict: 发现的技能名称到类的映射。
        """
        from app.core.registry.discovery import discover_and_register
        return discover_and_register(package, self, BaseSkill)


def register_skill(name: str = None, registry: SkillRegistry = None):
    """技能注册装饰器。

    将技能类注册到指定或全局注册表。

    Args:
        name: 自定义注册名称，默认使用类属性 name。
        registry: 目标注册表，默认使用全局注册表。

    Returns:
        Callable: 装饰器函数。

    Example:
        ```python
        @register_skill()
        class MySkill(BaseSkill):
            name = "my_skill"
        ```
    """
    def decorator(cls: Type[BaseSkill]) -> Type[BaseSkill]:
        reg = registry or _global_registry
        reg.register(name or cls.name, cls)
        return cls
    return decorator


# 全局技能注册表实例
_global_registry = SkillRegistry()
