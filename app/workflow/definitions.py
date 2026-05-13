from typing import Any, Dict, List, Optional

from app.workflow.activities import ACTIVITY_MAP
from app.workflow.pipeline.executor import ActivityRegistry, WorkflowPipeline
from app.workflow.pipeline.loader import PipelineLoader
from app.workflow.pipeline.models import PipelineConfig


class DevWorkflow:
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or self._load_default_config()
        self.activity_registry = ActivityRegistry()
        self._register_activities()
        self.pipeline = WorkflowPipeline(
            config=self.config,
            activity_registry=self.activity_registry,
        )

    def _load_default_config(self) -> PipelineConfig:
        loader = PipelineLoader()
        return loader.load("workflow-pipeline")

    def _register_activities(self) -> None:
        for name, func in ACTIVITY_MAP.items():
            self.activity_registry.register(name, func)

    async def run(
        self,
        project_id: str,
        requirement: str,
    ) -> Dict[str, Any]:
        inputs = {"requirement": requirement}
        results = await self.pipeline.run(
            project_id=project_id,
            inputs=inputs,
        )
        return {
            "project_id": project_id,
            "stages": {
                stage_id: {
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                    "duration_ms": result.duration_ms,
                }
                for stage_id, result in results.items()
            },
        }

    def get_stage_status(self, stage_id: str) -> Optional[Dict[str, Any]]:
        stage = self.config.get_stage(stage_id)
        if not stage:
            return None
        return {
            "id": stage.id,
            "name": stage.name,
            "agent": stage.agent,
            "activity": stage.activity,
            "requires_approval": stage.requires_approval,
        }

    def list_stages(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": stage.id,
                "name": stage.name,
                "agent": stage.agent,
                "requires_approval": stage.requires_approval,
            }
            for stage in self.config.stages
        ]
