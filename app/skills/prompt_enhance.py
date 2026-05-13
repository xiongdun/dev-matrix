from typing import Any, Dict

from app.skills.base import BaseSkill, SkillResult


class PromptEnhanceSkill(BaseSkill):
    name = "prompt_enhance"
    description = "Enhance prompts with additional context and structure"

    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        prompt = context.get("prompt", "")
        extra_context = context.get("context", {})

        enhanced = self._enhance(prompt, extra_context)

        return SkillResult(
            output=enhanced,
            metadata={"original_length": len(prompt), "enhanced_length": len(enhanced)},
        )

    def _enhance(self, prompt: str, context: Dict[str, Any]) -> str:
        parts = ["You are an expert software engineer."]

        if "language" in context:
            parts.append(f"Primary language: {context['language']}.")
        if "framework" in context:
            parts.append(f"Framework: {context['framework']}.")
        if "style_guide" in context:
            parts.append(f"Follow style guide: {context['style_guide']}.")

        parts.append("\n--- Task ---\n")
        parts.append(prompt)
        parts.append("\n--- Instructions ---\n")
        parts.append("Provide clear, well-structured, production-ready output.")

        return "\n".join(parts)
