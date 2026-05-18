"""验证技能模块。

实现 ValidationSkill，用于根据规则验证内容。

主要类：
    - ValidationSkill: 验证技能。

使用示例：
    ```python
    from app.skills.validation import ValidationSkill

    skill = ValidationSkill()
    result = await skill.execute({
        "content": "Design document with API section",
        "rules": ["design", "api", "data model"]
    })
    print(result.output)  # {"valid": True, "errors": []}
    ```
"""

from typing import Any, Dict

from app.skills.base import BaseSkill, SkillResult


class ValidationSkill(BaseSkill):
    """验证技能，根据规则验证内容。

    检查内容中是否包含所有必需的章节/关键字。

    Attributes:
        name: 技能名称，固定为 "validation"。
        description: 技能描述。

    Example:
        ```python
        skill = ValidationSkill()
        result = await skill.execute({
            "content": "Document content...",
            "rules": ["design", "api"]
        })
        print(result.output["valid"])  # True/False
        ```
    """

    name = "validation"
    description = "Validate content against a set of rules"

    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        """执行内容验证。

        检查内容中是否包含所有规则指定的关键字（不区分大小写）。

        Args:
            context: 执行上下文，包含：
                - content: 要验证的内容字符串。
                - rules: 必需章节/关键字列表。

        Returns:
            SkillResult: 验证结果，output 为 {"valid": bool, "errors": list}。
        """
        content = context.get("content", "")
        rules = context.get("rules", [])
        content_lower = content.lower()

        # 检查每个规则是否存在于内容中
        errors = []
        for rule in rules:
            if rule.lower() not in content_lower:
                errors.append(f"Missing required section: {rule}")

        return SkillResult(
            output={"valid": len(errors) == 0, "errors": errors},
            metadata={"rule_count": len(rules), "error_count": len(errors)},
        )
