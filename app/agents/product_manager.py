from typing import Any, Dict

from app.agents.base import BaseAgent, Proposal, ValidationResult


class ProductManagerAgent(BaseAgent):
    name = "product_manager"
    description = (
        "Generates Product Requirement Documents (PRD) from analyzed requirements"
    )
    system_prompt = (
        "You are an expert Product Manager. Your role is to create comprehensive "
        "Product Requirement Documents (PRD) based on analyzed requirements. "
        "Include: overview, goals, user personas, user stories, feature list, "
        "metrics, and roadmap. Be clear and actionable."
    )

    async def generate_proposal(
        self, project_id: str, context: Dict[str, Any]
    ) -> Proposal:
        state = self.read_state(project_id)
        requirements = state.get("requirement_analysis", "")

        prompt = (
            f"Create a comprehensive PRD based on the following analyzed requirements. "
            f"Include: overview, goals, user personas, user stories, feature list, "
            f"metrics, and roadmap.\n\n"
            f"Requirements:\n{requirements}"
        )

        # 优先使用 SDK，回退到 LLMRouter
        if self._sdk_options is not None:
            response = await self.sdk_query(prompt=prompt, max_turns=3)
        else:
            response = await self.llm_router.complete(prompt)

        return Proposal(
            agent_name=self.name,
            content=response,
            metadata={
                "phase": "prd_generation",
                "sdk_used": self._sdk_options is not None,
            },
        )

    async def validate_output(
        self, project_id: str, proposal: Proposal
    ) -> ValidationResult:
        content = proposal.content.lower()
        errors = []
        if "overview" not in content:
            errors.append("Missing overview section")
        if "user story" not in content and "user stories" not in content:
            errors.append("Missing user stories")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
