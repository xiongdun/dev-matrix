"""自动发现与注册模块。

提供 discover_and_register 函数，用于自动扫描包中的类并注册到注册表。

主要函数：
    - discover_and_register: 自动发现并注册类。

使用示例：
    ```python
    from app.core.registry.discovery import discover_and_register
    from app.core.registry.base import Registry
    from app.skills.base import BaseSkill

    registry = Registry[BaseSkill]()
    registered = discover_and_register("app.skills", registry, BaseSkill)
    print(f"Registered {len(registered)} skills")
    ```
"""

import importlib
import pkgutil
from typing import List, Type

from app.core.registry.base import Registry


def discover_and_register(
    package_name: str, registry: Registry, base_class: Type
) -> List[str]:
    """自动扫描包中的类并注册到注册表。

    遍历指定包的所有模块，查找继承自 base_class 的类，
    使用其 name 属性（或类名）作为注册名称。

    Args:
        package_name: 要扫描的包名。
        registry: 目标注册表。
        base_class: 要查找的基类。

    Returns:
        List[str]: 成功注册的名称列表。
    """
    registered: List[str] = []
    try:
        package = importlib.import_module(package_name)
    except ImportError:
        return registered

    # 遍历包中的所有模块
    for _, module_name, is_pkg in pkgutil.iter_modules(
        package.__path__, package.__name__ + "."
    ):
        if is_pkg:
            continue
        try:
            module = importlib.import_module(module_name)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, base_class)
                    and attr is not base_class
                ):
                    name = getattr(attr, "name", attr_name)
                    registry.register(name, attr)
                    registered.append(name)
        except Exception:
            pass

    return registered
