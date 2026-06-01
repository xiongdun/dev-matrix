from typing import Any

from app.agents.base import BaseAgent, Proposal, ValidationResult


class BusinessAnalystAgent(BaseAgent):
    name = "business_analyst"
    description = "Analyzes raw requirements and produces structured requirement documents"
    system_prompt = (
        "You are an expert Business Analyst. Your role is to analyze raw requirements "
        "and produce structured requirement documents including: functional "
        "requirements, non-functional requirements, user stories, and acceptance "
        "criteria. Be thorough and precise in your analysis."
    )

    async def generate_proposal(self, project_id: str, context: dict[str, Any]) -> Proposal:
        state = self.read_state(project_id)
        raw_input = (
            context.get("raw_input") or state.get("raw_input") or state.get("requirement", "")
        )

        prompt = (
            f"Analyze the following requirement and produce a structured requirement "
            f"document. Include: functional requirements, non-functional requirements, "
            f"user stories, and acceptance criteria.\n\n"
            f"Requirement: {raw_input}"
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
                "phase": "requirement_analysis",
                "sdk_used": self._sdk_options is not None,
            },
        )

    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        content = proposal.content
        errors = []
        if "functional" not in content.lower():
            errors.append("Missing functional requirements section")
        if "acceptance" not in content.lower():
            errors.append("Missing acceptance criteria")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
