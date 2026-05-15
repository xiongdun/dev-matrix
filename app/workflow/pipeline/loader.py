"""流水线配置加载器模块。

提供 PipelineLoader 类，从 YAML 文件加载和保存流水线配置。

主要类：
    - PipelineLoader: 流水线配置加载器。

使用示例：
    ```python
    from app.workflow.pipeline.loader import PipelineLoader

    loader = PipelineLoader("config")
    config = loader.load("workflow-pipeline")
    loader.save(config, "workflow-pipeline")
    ```
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from app.workflow.pipeline.models import PipelineConfig


class PipelineLoader:
    """流水线配置加载器，从 YAML 文件加载和保存配置。

    Attributes:
        config_dir: 配置文件目录路径。

    Example:
        ```python
        loader = PipelineLoader("config")
        config = loader.load("workflow-pipeline")
        config2 = loader.load_from_string(yaml_content)
        loader.save(config, "workflow-pipeline")
        ```
    """

    def __init__(self, config_dir: Optional[str] = None):
        """初始化加载器。

        Args:
            config_dir: 配置目录路径，默认使用 "config"。
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config")

    def load(self, name: str = "workflow-pipeline") -> PipelineConfig:
        """从 YAML 文件加载流水线配置。

        Args:
            name: 配置文件名（不含扩展名）。

        Returns:
            PipelineConfig: 流水线配置。

        Raises:
            FileNotFoundError: 配置文件不存在时抛出。
        """
        file_path = self.config_dir / f"{name}.yaml"
        if not file_path.exists():
            raise FileNotFoundError(f"Pipeline config not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        return PipelineConfig.from_dict(data)

    def load_from_string(self, content: str) -> PipelineConfig:
        """从 YAML 字符串加载流水线配置。

        Args:
            content: YAML 字符串。

        Returns:
            PipelineConfig: 流水线配置。
        """
        data = yaml.safe_load(content)
        return PipelineConfig.from_dict(data)

    def save(self, config: PipelineConfig, name: str = "workflow-pipeline") -> None:
        """保存流水线配置到 YAML 文件。

        Args:
            config: 流水线配置。
            name: 配置文件名（不含扩展名）。
        """
        file_path = self.config_dir / f"{name}.yaml"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        content = yaml.dump(
            config.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        file_path.write_text(content, encoding="utf-8")
