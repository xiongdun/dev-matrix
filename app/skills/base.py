from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SkillResult:
    output: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


@dataclass
class SkillConfig:
    timeout: int = 30
    retry_count: int = 0
    parameters: Dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    name: str = "base"
    description: str = ""

    def __init__(self, config: Optional[SkillConfig] = None):
        self.config = config or SkillConfig()

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        raise NotImplementedError

    def health_check(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "config": {
                "timeout": self.config.timeout,
                "retry_count": self.config.retry_count,
            },
        }
