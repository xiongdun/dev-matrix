from typing import Any

from app.agents.base import BaseAgent, Proposal, ValidationResult


class ProjectManagerAgent(BaseAgent):
    """项目经理 Agent。

    负责管理项目生命周期，协调各角色 Agent 协作执行工作流。
    核心职责包括：
        - 创建、查询、更新、关闭项目
        - 将工作分配给 BusinessAnalyst、ProductManager、Architect 等 Agent
        - 监控各 Agent 任务执行状态，生成项目整体进度报告
    """

    name = "project_manager"
    description = (
        "管理项目生命周期，协调各角色 Agent 协作执行工作流。"
        "负责创建/跟踪/关闭项目，分配任务给各角色 Agent，监控整体进度。"
    )
    system_prompt = (
        "You are an expert Project Manager. Your role is to manage project lifecycle, "
        "coordinate specialized agents (Business Analyst, Product Manager, Architect, "
        "Developer, QA), assign tasks, and track overall progress. "
        "Be organized, proactive, and ensure timely delivery."
    )

    async def generate_proposal(self, project_id: str, context: dict[str, Any]) -> Proposal:
        """生成项目管理提案。

        根据项目上下文生成项目计划、任务分配方案或进度报告。

        Args:
            project_id: 项目 ID。
            context: 上下文字典，可能包含 action（create_plan/assign_task/get_report）。

        Returns:
            Proposal: 生成的项目管理提案。
        """
        state = self.read_state(project_id)
        action = context.get("action", "create_plan")

        if action == "create_plan":
            prompt = self._build_plan_prompt(project_id, state, context)
        elif action == "assign_task":
            prompt = self._build_assign_prompt(project_id, state, context)
        elif action == "get_report":
            prompt = self._build_report_prompt(project_id, state, context)
        else:
            prompt = self._build_plan_prompt(project_id, state, context)

        if self._sdk_options is not None:
            response = await self.sdk_query(prompt=prompt, max_turns=3)
        else:
            response = await self.llm_router.complete(prompt)

        return Proposal(
            agent_name=self.name,
            content=response,
            metadata={
                "phase": "project_management",
                "action": action,
                "sdk_used": self._sdk_options is not None,
            },
        )

    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        """验证项目管理提案输出。

        检查提案是否包含必要的项目管理要素。

        Args:
            project_id: 项目 ID。
            proposal: 要验证的提案。

        Returns:
            ValidationResult: 验证结果。
        """
        content = proposal.content.lower()
        errors = []
        action = proposal.metadata.get("action", "create_plan")

        if action == "create_plan":
            if "plan" not in content and "schedule" not in content:
                errors.append("Missing project plan or schedule")
            if "task" not in content:
                errors.append("Missing task breakdown")
        elif action == "assign_task":
            if "assign" not in content and "responsible" not in content:
                errors.append("Missing task assignment details")
        elif action == "get_report":
            if "progress" not in content and "status" not in content:
                errors.append("Missing progress or status information")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def _build_plan_prompt(
        self, project_id: str, state: dict[str, Any], context: dict[str, Any]
    ) -> str:
        """构建项目计划提示词。"""
        requirements = state.get("requirement_analysis", "")
        prd = state.get("prd", "")
        return (
            f"Create a comprehensive project plan for project '{project_id}'.\n\n"
            f"Requirements:\n{requirements}\n\n"
            f"PRD:\n{prd}\n\n"
            f"Include: project phases, milestones, task breakdown, "
            f"agent assignments (Business Analyst, Product Manager, Architect, Developer, QA), "
            f"estimated timelines, and dependencies."
        )

    def _build_assign_prompt(
        self, project_id: str, state: dict[str, Any], context: dict[str, Any]
    ) -> str:
        """构建任务分配提示词。"""
        task = context.get("task", "")
        target_agent = context.get("target_agent", "")
        return (
            f"Assign the following task for project '{project_id}':\n\n"
            f"Task: {task}\n"
            f"Target Agent: {target_agent}\n\n"
            f"Provide: detailed instructions, expected deliverables, "
            f"deadline, and success criteria."
        )

    def _build_report_prompt(
        self, project_id: str, state: dict[str, Any], context: dict[str, Any]
    ) -> str:
        """构建进度报告提示词。"""
        return (
            f"Generate a project progress report for project '{project_id}'.\n\n"
            f"Current State:\n{state}\n\n"
            f"Include: overall progress percentage, completed tasks, "
            f"in-progress tasks, blocked items, risks, and next steps."
        )
