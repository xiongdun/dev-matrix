import os
from pathlib import Path
from typing import Dict, List, Optional

from app.prompts.engine import Jinja2PromptTemplate
from app.prompts.registry import PromptRegistry


class PromptLoader:
    def __init__(self, registry: PromptRegistry, templates_dir: Optional[str] = None):
        self.registry = registry
        self.templates_dir = Path(templates_dir) if templates_dir else Path(__file__).parent / "templates"

    def load_file(self, file_path: Path) -> Optional[Jinja2PromptTemplate]:
        if not file_path.exists() or not file_path.suffix == ".j2":
            return None

        name = file_path.stem
        source = file_path.read_text(encoding="utf-8")
        description = ""

        lines = source.splitlines()
        if lines and lines[0].startswith("{#"):
            for line in lines[1:]:
                if line.strip().startswith("#"):
                    description += line.strip().lstrip("#").strip() + " "
                elif "#}" in line:
                    break

        template = Jinja2PromptTemplate(
            name=name,
            source=source,
            description=description.strip(),
        )
        self.registry.register(name, template, {"file": str(file_path), "description": description.strip()})
        return template

    def load_all(self) -> Dict[str, Jinja2PromptTemplate]:
        loaded: Dict[str, Jinja2PromptTemplate] = {}
        if not self.templates_dir.exists():
            return loaded

        for file_path in self.templates_dir.iterdir():
            template = self.load_file(file_path)
            if template:
                loaded[template.name] = template

        return loaded

    def load_by_name(self, name: str) -> Optional[Jinja2PromptTemplate]:
        file_path = self.templates_dir / f"{name}.j2"
        return self.load_file(file_path)

    def list_available(self) -> List[str]:
        if not self.templates_dir.exists():
            return []
        return [f.stem for f in self.templates_dir.iterdir() if f.suffix == ".j2"]
