import importlib
import pkgutil
from typing import List, Type

from app.core.registry.base import Registry


def discover_and_register(package_name: str, registry: Registry, base_class: Type) -> List[str]:
    """Auto-discover classes in a package and register them to a registry."""
    registered: List[str] = []
    try:
        package = importlib.import_module(package_name)
    except ImportError:
        return registered

    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
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
