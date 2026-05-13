from typing import Any, Dict

from app.agents.base import BaseAgent, Proposal, ValidationResult


class DeveloperAgent(BaseAgent):
    name = "developer"
    description = "Generates code patches based on architecture design"

    async def generate_proposal(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        state = self.read_state(project_id)
        architecture = state.get("architecture", "")
        prompt = (
            f"You are a Senior Developer. Based on the following architecture design, "
            f"generate implementation code patches. Include: file changes, code diffs, "
            f"and new files to create. Use unified diff format where possible.\n\n"
            f"Architecture:\n{architecture}"
        )
        response = await self.llm_router.complete(prompt)
        return Proposal(
            agent_name=self.name,
            content=response,
            metadata={"phase": "patch_generation"},
        )

    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        content = proposal.content.lower()
        errors = []
        if "diff" not in content and "code" not in content:
            errors.append("Missing code changes")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
