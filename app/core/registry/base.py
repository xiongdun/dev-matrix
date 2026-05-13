from typing import Dict, Type, Callable, Any, TypeVar, Generic

T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self):
        self._items: Dict[str, Type[T]] = {}

    def register(self, name: str, cls: Type[T]) -> None:
        self._items[name] = cls

    def get(self, name: str) -> Type[T]:
        if name not in self._items:
            raise KeyError(f"Item '{name}' not found in registry")
        return self._items[name]

    def list(self) -> Dict[str, Type[T]]:
        return self._items.copy()

    def exists(self, name: str) -> bool:
        return name in self._items

    def unregister(self, name: str) -> None:
        if name in self._items:
            del self._items[name]


def register_in(registry: Registry, name: str = None) -> Callable:
    def decorator(cls: Type) -> Type:
        registry.register(name or cls.__name__, cls)
        return cls
    return decorator
