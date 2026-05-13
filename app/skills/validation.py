from typing import Any, Dict, List

from app.skills.base import BaseSkill, SkillResult


class ValidationSkill(BaseSkill):
    name = "validation"
    description = "Validate content against a set of rules"

    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        content = context.get("content", "")
        rules = context.get("rules", [])
        content_lower = content.lower()

        errors = []
        for rule in rules:
            if rule.lower() not in content_lower:
                errors.append(f"Missing required section: {rule}")

        return SkillResult(
            output={"valid": len(errors) == 0, "errors": errors},
            metadata={"rule_count": len(rules), "error_count": len(errors)},
        )
