from typing import Any, Dict

from app.agents.base import BaseAgent, Proposal, ValidationResult


class QAAgent(BaseAgent):
    name = "qa"
    description = "Generates and executes tests for the generated patches"

    async def generate_proposal(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        state = self.read_state(project_id)
        patches = state.get("patches", "")
        prompt = (
            f"You are a QA Engineer. Based on the following code patches, generate "
            f"comprehensive test cases. Include: unit tests, integration tests, "
            f"edge cases, and test execution plan.\n\n"
            f"Patches:\n{patches}"
        )
        response = await self.llm_router.complete(prompt)
        return Proposal(
            agent_name=self.name,
            content=response,
            metadata={"phase": "test_generation"},
        )

    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        content = proposal.content.lower()
        errors = []
        if "test" not in content:
            errors.append("Missing test cases")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
