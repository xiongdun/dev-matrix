"""Code Reviewer Agent - 智能代码审查。"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from app.agents.base import Agent, AgentRegistry
from app.prompts.code_review import (
    CODE_REVIEW_SYSTEM_PROMPT,
    build_code_review_prompt,
)
from app.llm.client import LLMClient

logger = logging.getLogger(__name__)


@AgentRegistry.register("code_reviewer")
class CodeReviewerAgent(Agent):
    """代码审查 Agent，使用 LLM 对代码补丁进行质量审查。"""

    name = "code_reviewer"
    display_name = "Code Reviewer"
    description = "智能代码审查专家，自动检测代码质量、安全漏洞和性能问题"

    def __init__(self) -> None:
        super().__init__()
        self.llm_client = LLMClient()

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码审查。

        Args:
            context: 包含以下字段：
                - diff: 代码 diff 字符串
                - project_context: 项目上下文（可选）
                - model: 指定 LLM 模型（可选）

        Returns:
            Dict: 审查报告，包含 score、issues、improvements 等。
        """
        diff = context.get("diff", "")
        project_context = context.get("project_context", "")
        model = context.get("model")

        if not diff:
            return {
                "score": 0,
                "summary": "没有提供代码 diff",
                "issues": [],
                "improvements": [],
            }

        prompt = build_code_review_prompt(diff, project_context)

        start_time = time.time()
        try:
            response = await self.llm_client.chat_completion(
                system_prompt=CODE_REVIEW_SYSTEM_PROMPT,
                user_prompt=prompt,
                model=model,
                temperature=0.2,
            )
            duration_ms = int((time.time() - start_time) * 1000)

            # 解析 JSON 响应
            content = response.get("content", "")
            # 尝试提取 JSON 部分（LLM 可能会包裹在 markdown 代码块中）
            json_str = self._extract_json(content)
            report = json.loads(json_str)

            # 确保必要字段存在
            report.setdefault("score", 0)
            report.setdefault("summary", "")
            report.setdefault("issues", [])
            report.setdefault("improvements", [])

            # 标准化问题格式
            for issue in report["issues"]:
                issue.setdefault("line", None)
                issue.setdefault("file", "")

            report["duration_ms"] = duration_ms
            report["llm_model"] = response.get("model", model or "default")

            logger.info(
                "Code review completed: score=%d, issues=%d, duration=%dms",
                report["score"],
                len(report["issues"]),
                duration_ms,
            )

            return report

        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON: %s", e)
            return {
                "score": 0,
                "summary": f"审查结果解析失败：{e}",
                "issues": [],
                "improvements": [],
                "error": str(e),
                "raw_response": content if "content" in locals() else "",
            }
        except Exception as e:
            logger.exception("Code review failed")
            return {
                "score": 0,
                "summary": f"审查失败：{e}",
                "issues": [],
                "improvements": [],
                "error": str(e),
            }

    def _extract_json(self, content: str) -> str:
        """从 LLM 响应中提取 JSON 字符串。"""
        content = content.strip()

        # 尝试查找 markdown 代码块
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                return content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                return content[start:end].strip()

        # 尝试查找 JSON 对象边界
        if content.startswith("{") and content.endswith("}"):
            return content

        # 查找第一个 { 和最后一个 }
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return content[start:end + 1]

        return content

    def get_system_prompt(self) -> str:
        return CODE_REVIEW_SYSTEM_PROMPT
