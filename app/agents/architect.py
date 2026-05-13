from typing import Any, Dict

from app.agents.base import BaseAgent, Proposal, ValidationResult


class ArchitectAgent(BaseAgent):
    name = "architect"
    description = "Performs code impact analysis and designs technical solutions"

    async def generate_proposal(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        state = self.read_state(project_id)
        prd = state.get("prd", "")
        repo_path = context.get("repo_path", "")
        prompt = (
            f"You are a Software Architect. Based on the following PRD, analyze the "
            f"technical impact and design a solution. Include: system design, "
            f"component diagram, API design, data model changes, and affected files.\n\n"
            f"PRD:\n{prd}\n\n"
            f"Repository: {repo_path}"
        )
        response = await self.llm_router.complete(prompt)
        return Proposal(
            agent_name=self.name,
            content=response,
            metadata={"phase": "architecture_design"},
        )

    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        content = proposal.content.lower()
        errors = []
        if "design" not in content:
            errors.append("Missing design section")
        if "api" not in content:
            errors.append("Missing API design")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
