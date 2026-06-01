"""Code Reviewer Agent - 智能代码审查。"""

import json
import logging
import time
from typing import Any

from app.agents.base import BaseAgent, Proposal, ValidationResult
from app.prompts.code_review import (
    CODE_REVIEW_SYSTEM_PROMPT,
    build_code_review_prompt,
)

logger = logging.getLogger(__name__)


class CodeReviewerAgent(BaseAgent):
    """代码审查 Agent，使用 LLM 对代码补丁进行质量审查。"""

    name = "code_reviewer"
    description = "智能代码审查专家，自动检测代码质量、安全漏洞和性能问题"
    system_prompt = CODE_REVIEW_SYSTEM_PROMPT

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
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

        # 1. 静态分析（快速筛选）
        static_issues = []
        try:
            from app.static_analysis.engine import StaticAnalysisEngine

            engine = StaticAnalysisEngine()
            static_issues = engine.analyze_diff(diff)
            logger.info("Static analysis found %d issues", len(static_issues))
        except Exception as e:
            logger.warning("Static analysis failed: %s", e)

        prompt = build_code_review_prompt(diff, project_context)

        start_time = time.time()
        try:
            messages = [
                {"role": "system", "content": CODE_REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            content = await self.llm_router.chat(
                messages=messages,
                temperature=0.2,
            )
            duration_ms = int((time.time() - start_time) * 1000)

            # 解析 JSON 响应
            # 尝试提取 JSON 部分（LLM 可能会包裹在 markdown 代码块中）
            json_str = self._extract_json(content)
            report = json.loads(json_str)

            # 确保必要字段存在
            report.setdefault("score", 0)
            report.setdefault("summary", "")
            report.setdefault("issues", [])
            report.setdefault("improvements", [])

            # 3. 合并结果（静态分析结果优先）
            merged_issues = static_issues.copy()
            static_files = {i["file"] + str(i.get("line")) for i in static_issues}

            for issue in report["issues"]:
                issue.setdefault("line", None)
                issue.setdefault("file", "")
                key = issue["file"] + str(issue.get("line"))
                if key not in static_files:
                    merged_issues.append(issue)

            report["issues"] = merged_issues
            report["duration_ms"] = duration_ms
            report["llm_model"] = model or self.llm_router.model or "default"
            report["static_analysis_count"] = len(static_issues)

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
            # 即使 LLM 失败，也返回静态分析结果
            if static_issues:
                return {
                    "score": max(0, 100 - len(static_issues) * 10),
                    "summary": f"LLM 审查失败，仅显示静态分析结果：{e}",
                    "issues": static_issues,
                    "improvements": [],
                    "error": str(e),
                }
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
            return content[start : end + 1]

        return content

    def get_system_prompt(self) -> str:
        return CODE_REVIEW_SYSTEM_PROMPT

    async def generate_proposal(self, project_id: str, context: dict[str, Any]) -> Proposal:
        """生成代码审查提案。"""
        diff = context.get("diff", "")
        report = await self.execute({"diff": diff, "project_context": context})
        return Proposal(
            agent_name=self.name,
            content=report.get("summary", ""),
            metadata={"score": report.get("score"), "issues": report.get("issues", [])},
        )

    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        """验证代码审查输出。"""
        score = proposal.metadata.get("score", 0)
        is_valid = score >= 60 if score is not None else True
        return ValidationResult(
            is_valid=is_valid,
            errors=["代码质量评分低于60"] if not is_valid else [],
            warnings=[],
        )
