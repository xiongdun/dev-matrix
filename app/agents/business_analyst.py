import json
from typing import Any, Dict

from app.agents.base import BaseAgent, Proposal, ValidationResult


class BusinessAnalystAgent(BaseAgent):
    name = "business_analyst"
    description = "Analyzes raw requirements and produces structured requirement documents"

    async def generate_proposal(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        raw_input = context.get("raw_input", "")
        prompt = (
            f"You are a Business Analyst. Analyze the following requirement and produce "
            f"a structured requirement document with: functional requirements, "
            f"non-functional requirements, user stories, and acceptance criteria.\n\n"
            f"Requirement: {raw_input}"
        )
        response = await self.llm_router.complete(prompt)
        return Proposal(
            agent_name=self.name,
            content=response,
            metadata={"phase": "requirement_analysis"},
        )

    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        content = proposal.content
        errors = []
        if "functional" not in content.lower():
            errors.append("Missing functional requirements section")
        if "acceptance" not in content.lower():
            errors.append("Missing acceptance criteria")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
