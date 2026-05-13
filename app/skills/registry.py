from typing import Dict, Optional, Type

from app.core.registry.base import Registry
from app.skills.base import BaseSkill, SkillConfig


class SkillRegistry(Registry[BaseSkill]):
    def create(self, name: str, config: Optional[SkillConfig] = None) -> BaseSkill:
        skill_class = self.get(name)
        return skill_class(config)

    def discover(self, package: str = "app.skills") -> Dict[str, Type[BaseSkill]]:
        from app.core.registry.discovery import discover_and_register
        return discover_and_register(package, self, BaseSkill)


def register_skill(name: str = None, registry: SkillRegistry = None):
    def decorator(cls: Type[BaseSkill]) -> Type[BaseSkill]:
        reg = registry or _global_registry
        reg.register(name or cls.name, cls)
        return cls
    return decorator


_global_registry = SkillRegistry()
