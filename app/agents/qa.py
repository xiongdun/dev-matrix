from typing import Any

from app.agents.base import BaseAgent, Proposal, ValidationResult


class QAAgent(BaseAgent):
    name = "qa"
    description = "Generates and executes tests for the generated patches"
    system_prompt = (
        "You are an expert QA Engineer. Your role is to generate comprehensive test "
        "cases based on code patches. Include: unit tests, integration tests, edge "
        "cases, and test execution plan. Be thorough and cover all scenarios."
    )

    async def generate_proposal(self, project_id: str, context: dict[str, Any]) -> Proposal:
        state = self.read_state(project_id)
        patches = state.get("patches", "")

        prompt = (
            f"Based on the following code patches, generate comprehensive test "
            f"cases. Include: unit tests, integration tests, edge cases, and test "
            f"execution plan.\n\n"
            f"Patches:\n{patches}"
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
                "phase": "test_generation",
                "sdk_used": self._sdk_options is not None,
            },
        )

    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        content = proposal.content.lower()
        errors = []
        if "test" not in content:
            errors.append("Missing test cases")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
