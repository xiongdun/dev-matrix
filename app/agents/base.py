import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.llm.router import LLMRouter
from app.state.repository import StateRepository


@dataclass
class Proposal:
    agent_name: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    name: str = "base"
    description: str = "Base agent"

    def __init__(
        self,
        llm_router: LLMRouter,
        state_repository: StateRepository,
    ):
        self.llm_router = llm_router
        self.state_repository = state_repository

    def read_state(self, project_id: str) -> Dict[str, Any]:
        state = self.state_repository.get_state(project_id)
        if state is None or not state.state_json:
            return {}
        return json.loads(state.state_json)

    def write_state(self, project_id: str, state_dict: Dict[str, Any], status: Optional[str] = None):
        self.state_repository.update_state(
            project_id=project_id,
            state_json=json.dumps(state_dict, ensure_ascii=False),
            status=status,
        )

    @abstractmethod
    async def generate_proposal(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        pass

    @abstractmethod
    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        pass

    async def run(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        proposal = await self.generate_proposal(project_id, context)
        validation = await self.validate_output(project_id, proposal)
        if not validation.is_valid:
            raise ValueError(f"Validation failed: {validation.errors}")
        return proposal
