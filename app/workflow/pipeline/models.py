"""流水线模型模块。

定义 PipelineStage 和 PipelineConfig 数据类，
提供从字典的序列化和反序列化方法。

主要类：
    - PipelineStage: 流水线阶段配置。
    - PipelineConfig: 流水线整体配置。

使用示例：
    ```python
    from app.workflow.pipeline.models import PipelineConfig

    config = PipelineConfig.from_dict({
        "name": "default",
        "version": "1.0.0",
        "stages": [...]
    })
    ```
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PipelineStage:
    """流水线阶段配置。

    Attributes:
        id: 阶段唯一标识。
        name: 阶段名称。
        agent: 执行 Agent 名称。
        activity: 执行活动名称。
        requires_approval: 是否需要审批。
        timeout_seconds: 执行超时时间（秒）。
        retries: 失败重试次数。
        condition: 执行条件表达式，可选。
        next_stages: 后续阶段 ID 列表。
        on_failure: 失败处理策略（abort/skip/retry）。
    """

    id: str
    name: str
    agent: str
    activity: str
    requires_approval: bool = True
    timeout_seconds: int = 300
    retries: int = 0
    condition: Optional[str] = None
    next_stages: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
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
            requires=data.get("requires", []),
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
            "requires": self.requires,
            "on_failure": self.on_failure,
        }

    def get_next_stages(self) -> List[str]:
        return self.next_stages


@dataclass
class PipelineConfig:
    """流水线整体配置。

    Attributes:
        name: 配置名称。
        version: 版本号。
        description: 配置描述。
        stages: 阶段列表。
        settings: 附加设置字典。
    """

    name: str
    version: str
    description: str = ""
    stages: List[PipelineStage] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """从字典创建流水线配置。

        Args:
            data: 配置字典。

        Returns:
            PipelineConfig: 流水线配置实例。
        """
        return cls(
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            stages=[PipelineStage.from_dict(s) for s in data.get("stages", [])],
            settings=data.get("settings", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典。

        Returns:
            Dict: 配置字典。
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "stages": [s.to_dict() for s in self.stages],
            "settings": self.settings,
        }

    def get_stage(self, stage_id: str) -> Optional[PipelineStage]:
        """按 ID 查找阶段。

        Args:
            stage_id: 阶段 ID。

        Returns:
            PipelineStage: 阶段配置，未找到返回 None。
        """
        for stage in self.stages:
            if stage.id == stage_id:
                return stage
        return None

    def get_first_stage(self) -> Optional[PipelineStage]:
        """获取第一个阶段。

        Returns:
            PipelineStage: 第一个阶段，空列表返回 None。
        """
        if self.stages:
            return self.stages[0]
        return None

    def get_next_stages(self, stage_id: str) -> List[PipelineStage]:
        """获取指定阶段的后续阶段。

        优先使用显式配置的 next_stages，否则按列表顺序返回下一个。

        Args:
            stage_id: 当前阶段 ID。

        Returns:
            List[PipelineStage]: 后续阶段列表。
        """
        stage = self.get_stage(stage_id)
        if not stage:
            return []
        if stage.next_stages:
            return [self.get_stage(sid) for sid in stage.next_stages if self.get_stage(sid)]
        idx = self.stages.index(stage)
        if idx + 1 < len(self.stages):
            return [self.stages[idx + 1]]
        return []
