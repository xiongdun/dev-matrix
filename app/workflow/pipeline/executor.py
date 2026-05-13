import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.workflow.pipeline.models import PipelineConfig, PipelineStage


@dataclass
class ActivityContext:
    project_id: str
    stage: PipelineStage
    state: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActivityResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


ActivityFunc = Callable[[ActivityContext], Any]


class ActivityRegistry:
    def __init__(self):
        self._activities: Dict[str, ActivityFunc] = {}

    def register(self, name: str, func: ActivityFunc) -> None:
        self._activities[name] = func

    def get(self, name: str) -> ActivityFunc:
        if name not in self._activities:
            raise KeyError(f"Activity '{name}' not registered")
        return self._activities[name]

    def list(self) -> List[str]:
        return list(self._activities.keys())

    def exists(self, name: str) -> bool:
        return name in self._activities


class WorkflowPipeline:
    def __init__(
        self,
        config: PipelineConfig,
        activity_registry: ActivityRegistry,
    ):
        self.config = config
        self.activities = activity_registry
        self._state: Dict[str, Any] = {}
        self._listeners: List[Callable[[str, Dict], None]] = []

    def add_listener(self, listener: Callable[[str, Dict], None]) -> None:
        self._listeners.append(listener)

    def _emit(self, event_type: str, data: Dict) -> None:
        for listener in self._listeners:
            try:
                listener(event_type, data)
            except Exception:
                pass

    async def execute_stage(
        self,
        project_id: str,
        stage: PipelineStage,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> ActivityResult:
        self._emit("stage_start", {"project_id": project_id, "stage": stage.id})

        if not self.activities.exists(stage.activity):
            result = ActivityResult(
                success=False,
                error=f"Activity '{stage.activity}' not found",
            )
            self._emit("stage_error", {"project_id": project_id, "stage": stage.id, "error": result.error})
            return result

        context = ActivityContext(
            project_id=project_id,
            stage=stage,
            state=self._state,
            inputs=inputs or {},
        )

        activity_func = self.activities.get(stage.activity)
        start = asyncio.get_event_loop().time()

        try:
            if asyncio.iscoroutinefunction(activity_func):
                output = await asyncio.wait_for(
                    activity_func(context),
                    timeout=stage.timeout_seconds,
                )
            else:
                output = activity_func(context)

            duration = (asyncio.get_event_loop().time() - start) * 1000
            result = ActivityResult(success=True, output=output, duration_ms=duration)
            self._emit("stage_complete", {"project_id": project_id, "stage": stage.id, "result": result})
            return result

        except asyncio.TimeoutError:
            duration = (asyncio.get_event_loop().time() - start) * 1000
            result = ActivityResult(
                success=False,
                error=f"Stage timed out after {stage.timeout_seconds}s",
                duration_ms=duration,
            )
            self._emit("stage_error", {"project_id": project_id, "stage": stage.id, "error": result.error})
            return result

        except Exception as e:
            duration = (asyncio.get_event_loop().time() - start) * 1000
            result = ActivityResult(success=False, error=str(e), duration_ms=duration)
            self._emit("stage_error", {"project_id": project_id, "stage": stage.id, "error": result.error})
            return result

    async def run(
        self,
        project_id: str,
        start_stage: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, ActivityResult]:
        results: Dict[str, ActivityResult] = {}

        current = self.config.get_stage(start_stage) if start_stage else self.config.get_first_stage()
        if not current:
            raise ValueError("No starting stage found")

        stage_inputs = inputs or {}

        while current:
            result = await self.execute_stage(project_id, current, stage_inputs)
            results[current.id] = result

            if not result.success:
                if current.on_failure == "abort":
                    break
                elif current.on_failure == "skip":
                    next_stages = self.config.get_next_stages(current.id)
                    current = next_stages[0] if next_stages else None
                    continue
                elif current.on_failure == "retry" and current.retries > 0:
                    for _ in range(current.retries):
                        result = await self.execute_stage(project_id, current, stage_inputs)
                        results[current.id] = result
                        if result.success:
                            break
                    if not result.success:
                        break

            stage_inputs = {"previous_output": result.output}
            next_stages = self.config.get_next_stages(current.id)
            current = next_stages[0] if next_stages else None

        return results
