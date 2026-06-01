"""通用注册表基础模块。

提供 Registry 泛型类，用于按名称存储和检索类。
支持通过装饰器或直接方法调用进行注册。

主要类/函数：
    - Registry: 通用注册表泛型类。
    - register_in: 注册装饰器工厂函数。

使用示例：
    ```python
    registry = Registry[BaseSkill]()

    @register_in(registry)
    class MySkill(BaseSkill):
        pass

    skill_cls = registry.get("MySkill")
    ```
"""

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    """通用注册表，用于按名称存储和检索类。

    提供集中管理插件式组件（如 Agent、Skill、LLM Provider）的方式，
    支持通过装饰器或直接方法调用进行注册。

    Attributes:
        _items: 内部存储的名称到类的映射字典。

    Example:
        ```python
        registry = Registry[BaseSkill]()

        @register_in(registry)
        class MySkill(BaseSkill):
            pass

        skill_cls = registry.get("MySkill")
        ```
    """

    def __init__(self):
        """初始化空注册表。"""
        self._items: dict[str, type[T]] = {}

    def register(self, name: str, cls: type[T]) -> None:
        """注册类到指定名称。

        Args:
            name: 注册名称。
            cls: 要注册的类。
        """
        self._items[name] = cls

    def get(self, name: str) -> type[T]:
        """按名称检索已注册的类。

        Args:
            name: 注册名称。

        Returns:
            Type[T]: 已注册的类。

        Raises:
            TypeError: name 不是字符串时抛出。
            KeyError: 名称未在注册表中找到时抛出。
        """
        if not isinstance(name, str):
            raise TypeError(f"Registry name must be a string, got {type(name).__name__}")
        if name not in self._items:
            raise KeyError(f"Item '{name}' not found in registry")
        return self._items[name]

    def list(self) -> dict[str, type[T]]:
        """返回所有已注册项的浅拷贝。

        Returns:
            Dict: 名称到类的映射字典的拷贝。
        """
        return self._items.copy()

    def exists(self, name: str) -> bool:
        """检查名称是否已注册。

        Args:
            name: 要检查的名称。

        Returns:
            bool: 是否已注册。
        """
        return name in self._items

    def unregister(self, name: str) -> None:
        """按名称移除已注册的项。

        Args:
            name: 要移除的名称。
        """
        if name in self._items:
            del self._items[name]


def register_in(registry: Registry, name: str | None = None) -> Callable:
    """注册装饰器，将类注册到指定注册表。

    Args:
        registry: 要注册到的 Registry 实例。
        name: 可选的自定义名称，默认使用类的 __name__。

    Returns:
        Callable: 装饰器函数，注册类并返回原类。

    Example:
        ```python
        registry = Registry[BaseSkill]()

        @register_in(registry, "custom_name")
        class MySkill(BaseSkill):
            pass
        ```
    """

    def decorator(cls: type) -> type:
        registry.register(name or cls.__name__, cls)
        return cls

    return decorator
