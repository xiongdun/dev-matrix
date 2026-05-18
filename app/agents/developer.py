from typing import Any, Dict

from app.agents.base import BaseAgent, Proposal, ValidationResult


class DeveloperAgent(BaseAgent):
    name = "developer"
    description = "Generates code patches based on architecture design"
    system_prompt = (
        "You are an expert Senior Developer. Your role is to generate implementation "
        "code patches based on architecture design. Include: file changes, code diffs, "
        "and new files to create. Use unified diff format where possible. "
        "Be precise and follow best practices."
    )

    async def generate_proposal(
        self, project_id: str, context: Dict[str, Any]
    ) -> Proposal:
        state = self.read_state(project_id)
        architecture = state.get("architecture", "")

        prompt = (
            f"Based on the following architecture design, generate implementation "
            f"code patches. Include: file changes, code diffs, and new files to "
            f"create. Use unified diff format where possible.\n\n"
            f"Architecture:\n{architecture}"
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
                "phase": "patch_generation",
                "sdk_used": self._sdk_options is not None,
            },
        )

    async def validate_output(
        self, project_id: str, proposal: Proposal
    ) -> ValidationResult:
        content = proposal.content.lower()
        errors = []
        if "diff" not in content and "code" not in content:
            errors.append("Missing code changes")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
