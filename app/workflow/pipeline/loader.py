from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from app.workflow.pipeline.models import PipelineConfig


class PipelineLoader:
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path("config")

    def load(self, name: str = "workflow-pipeline") -> PipelineConfig:
        file_path = self.config_dir / f"{name}.yaml"
        if not file_path.exists():
            raise FileNotFoundError(f"Pipeline config not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        return PipelineConfig.from_dict(data)

    def load_from_string(self, content: str) -> PipelineConfig:
        data = yaml.safe_load(content)
        return PipelineConfig.from_dict(data)

    def save(self, config: PipelineConfig, name: str = "workflow-pipeline") -> None:
        file_path = self.config_dir / f"{name}.yaml"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        content = yaml.dump(
            config.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        file_path.write_text(content, encoding="utf-8")
