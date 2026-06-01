"""提示增强技能模块。

实现 PromptEnhanceSkill，用于增强提示词，添加额外上下文和结构。

主要类：
    - PromptEnhanceSkill: 提示增强技能。

使用示例：
    ```python
    from app.skills.prompt_enhance import PromptEnhanceSkill

    skill = PromptEnhanceSkill()
    result = await skill.execute({
        "prompt": "Implement a login feature",
        "context": {"language": "Python", "framework": "FastAPI"}
    })
    ```
"""

from typing import Any

from app.skills.base import BaseSkill, SkillResult


class PromptEnhanceSkill(BaseSkill):
    """提示增强技能，为提示词添加额外上下文和结构。

    根据上下文中的语言、框架、风格指南等信息增强原始提示词。

    Attributes:
        name: 技能名称，固定为 "prompt_enhance"。
        description: 技能描述。

    Example:
        ```python
        skill = PromptEnhanceSkill()
        result = await skill.execute({
            "prompt": "Implement login",
            "context": {"language": "Python"}
        })
        print(result.output)  # 增强后的提示词
        ```
    """

    name = "prompt_enhance"
    description = "Enhance prompts with additional context and structure"

    async def execute(self, context: dict[str, Any]) -> SkillResult:
        """执行提示增强。

        Args:
            context: 执行上下文，包含：
                - prompt: 原始提示词。
                - context: 额外上下文字典，可包含 language、framework、style_guide。

        Returns:
            SkillResult: 增强后的提示词。
        """
        prompt = context.get("prompt", "")
        extra_context = context.get("context", {})

        enhanced = self._enhance(prompt, extra_context)

        return SkillResult(
            output=enhanced,
            metadata={"original_length": len(prompt), "enhanced_length": len(enhanced)},
        )

    def _enhance(self, prompt: str, context: dict[str, Any]) -> str:
        """增强提示词的内部方法。

        根据上下文信息构建结构化的增强提示词。

        Args:
            prompt: 原始提示词。
            context: 额外上下文字典。

        Returns:
            str: 增强后的提示词。
        """
        parts = ["You are an expert software engineer."]

        # 根据上下文添加语言、框架和风格指南信息
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
