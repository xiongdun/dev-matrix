from typing import Any, Dict

from app.agents.base import BaseAgent, Proposal, ValidationResult


class ProductManagerAgent(BaseAgent):
    name = "product_manager"
    description = "Generates Product Requirement Documents (PRD) from analyzed requirements"

    async def generate_proposal(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        state = self.read_state(project_id)
        requirements = state.get("requirement_analysis", "")
        prompt = (
            f"You are a Product Manager. Create a comprehensive PRD based on the "
            f"following analyzed requirements. Include: overview, goals, user personas, "
            f"user stories, feature list, metrics, and roadmap.\n\n"
            f"Requirements:\n{requirements}"
        )
        response = await self.llm_router.complete(prompt)
        return Proposal(
            agent_name=self.name,
            content=response,
            metadata={"phase": "prd_generation"},
        )

    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        content = proposal.content.lower()
        errors = []
        if "overview" not in content:
            errors.append("Missing overview section")
        if "user story" not in content and "user stories" not in content:
            errors.append("Missing user stories")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
