"""架构师 Agent 模块。

实现 ArchitectAgent，负责基于 PRD 进行代码影响分析和技术方案设计。
支持通过 code_search 技能获取相关代码上下文。

主要类：
    - ArchitectAgent: 架构师 Agent，执行架构设计任务。

使用示例：
    ```python
    from app.agents.architect import ArchitectAgent
    from app.llm.router import LLMRouter
    from app.state.repository import StateRepository

    agent = ArchitectAgent(llm_router=router, state_repository=repo)
    proposal = await agent.generate_proposal("proj_1", {"repo_path": "/path/to/repo"})
    ```
"""

from typing import Any, Dict

from app.agents.base import BaseAgent, Proposal, ValidationResult


class ArchitectAgent(BaseAgent):
    """架构师 Agent，执行代码影响分析和技术方案设计。

    基于 PRD 内容分析技术影响，设计系统架构、API、数据模型等。
    如果组合了 code_search 技能且提供了仓库路径，会自动检索相关代码上下文。

    Attributes:
        name: Agent 名称，固定为 "architect"。
        description: Agent 描述。

    Example:
        ```python
        agent = ArchitectAgent(llm_router=router, state_repository=repo)
        agent.use_skill(CodeSearchSkill())
        proposal = await agent.generate_proposal("proj_1", {
            "repo_path": "/path/to/repo"
        })
        ```
    """

    name = "architect"
    description = "Performs code impact analysis and designs technical solutions"

    async def generate_proposal(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        """生成架构设计提案。

        读取项目状态中的 PRD，可选地检索相关代码上下文，
        然后调用 LLM 生成架构设计提案。

        Args:
            project_id: 项目 ID。
            context: 上下文字典，可包含 repo_path 等。

        Returns:
            Proposal: 架构设计提案，包含设计内容和使用 code_search 的元数据。
        """
        state = self.read_state(project_id)
        prd = state.get("prd", "")
        repo_path = context.get("repo_path", "")

        # 尝试获取相关代码上下文
        code_context = ""
        if self.has_skill("code_search") and repo_path:
            try:
                result = await self.call_skill("code_search", {
                    "query": prd,
                    "repo_path": repo_path,
                })
                if result.success:
                    code_context = f"\n\nRelevant code context:\n{result.output}"
            except Exception:
                pass  # 代码搜索失败时不阻塞主流程

        # 构建提示词
        prompt = (
            f"You are a Software Architect. Based on the following PRD, analyze the "
            f"technical impact and design a solution. Include: system design, "
            f"component diagram, API design, data model changes, and affected files."
            f"{code_context}\n\n"
            f"PRD:\n{prd}\n\n"
            f"Repository: {repo_path}"
        )
        response = await self.llm_router.complete(prompt)
        return Proposal(
            agent_name=self.name,
            content=response,
            metadata={"phase": "architecture_design", "used_code_search": bool(code_context)},
        )

    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        """验证架构提案是否包含必要章节。

        检查提案内容是否包含 "design" 和 "api" 关键字。

        Args:
            project_id: 项目 ID。
            proposal: 要验证的提案。

        Returns:
            ValidationResult: 验证结果。
        """
        content = proposal.content.lower()
        errors = []
        if "design" not in content:
            errors.append("Missing design section")
        if "api" not in content:
            errors.append("Missing API design")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
