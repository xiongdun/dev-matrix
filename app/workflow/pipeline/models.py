from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PipelineStage:
    id: str
    name: str
    agent: str
    activity: str
    requires_approval: bool = True
    timeout_seconds: int = 300
    retries: int = 0
    condition: Optional[str] = None
    next_stages: List[str] = field(default_factory=list)
    on_failure: str = "abort"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineStage":
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            agent=data["agent"],
            activity=data["activity"],
            requires_approval=data.get("requires_approval", True),
            timeout_seconds=data.get("timeout_seconds", 300),
            retries=data.get("retries", 0),
            condition=data.get("condition"),
            next_stages=data.get("next_stages", []),
            on_failure=data.get("on_failure", "abort"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "agent": self.agent,
            "activity": self.activity,
            "requires_approval": self.requires_approval,
            "timeout_seconds": self.timeout_seconds,
            "retries": self.retries,
            "condition": self.condition,
            "next_stages": self.next_stages,
            "on_failure": self.on_failure,
        }


@dataclass
class PipelineConfig:
    name: str
    version: str
    description: str = ""
    stages: List[PipelineStage] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        return cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            stages=[PipelineStage.from_dict(s) for s in data.get("stages", [])],
            settings=data.get("settings", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "stages": [s.to_dict() for s in self.stages],
            "settings": self.settings,
        }

    def get_stage(self, stage_id: str) -> Optional[PipelineStage]:
        for stage in self.stages:
            if stage.id == stage_id:
                return stage
        return None

    def get_first_stage(self) -> Optional[PipelineStage]:
        if self.stages:
            return self.stages[0]
        return None

    def get_next_stages(self, stage_id: str) -> List[PipelineStage]:
        stage = self.get_stage(stage_id)
        if not stage:
            return []
        if stage.next_stages:
            return [self.get_stage(sid) for sid in stage.next_stages if self.get_stage(sid)]
        idx = self.stages.index(stage)
        if idx + 1 < len(self.stages):
            return [self.stages[idx + 1]]
        return []
