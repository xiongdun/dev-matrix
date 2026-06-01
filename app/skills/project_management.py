"""项目管理技能模块。

提供项目生命周期管理相关的技能，包括项目 CRUD、任务分配和进度跟踪。

主要技能：
    - ProjectCrudSkill: 项目创建、查询、更新、删除
    - TaskAssignSkill: 任务分配给指定 Agent
    - ProgressTrackSkill: 项目进度跟踪和报告生成
"""

import logging
from typing import Any

from app.skills.base import BaseSkill, SkillConfig, SkillResult
from app.state.models import ProjectModel, get_db

logger = logging.getLogger(__name__)


class ProjectCrudSkill(BaseSkill):
    """项目 CRUD 技能。

    支持创建、查询、更新和删除项目。
    """

    name = "project_crud"
    description = "Create, read, update, and delete projects"

    def __init__(self, config: SkillConfig = None):
        super().__init__(config)

    async def execute(self, context: dict[str, Any]) -> SkillResult:
        """执行项目 CRUD 操作。

        Args:
            context: 包含 action 和数据的上下文字典。
                action: "create" | "get" | "update" | "delete"
                其他字段根据 action 变化

        Returns:
            SkillResult: 操作结果。
        """
        action = context.get("action", "get")
        db = next(get_db())
        try:
            if action == "create":
                return self._create_project(context, db)
            elif action == "get":
                return self._get_project(context, db)
            elif action == "update":
                return self._update_project(context, db)
            elif action == "delete":
                return self._delete_project(context, db)
            elif action == "list":
                return self._list_projects(context, db)
            else:
                return SkillResult(
                    output=None,
                    success=False,
                    error=f"Unknown action: {action}",
                )
        except Exception as exc:
            logger.exception("Project CRUD skill failed")
            return SkillResult(output=None, success=False, error=str(exc))
        finally:
            db.close()

    def _create_project(self, context: dict[str, Any], db) -> SkillResult:
        """创建项目。"""
        project = ProjectModel(
            name=context.get("name", "Untitled"),
            description=context.get("description", ""),
            owner=context.get("owner", "project_manager"),
            priority=context.get("priority", "medium"),
            status=context.get("status", "planning"),
            progress=context.get("progress", 0),
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        logger.info("Created project id=%d name=%s", project.id, project.name)
        return SkillResult(
            output={
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
            },
            metadata={"action": "create"},
        )

    def _get_project(self, context: dict[str, Any], db) -> SkillResult:
        """查询项目。"""
        project_id = context.get("project_id")
        if not project_id:
            return SkillResult(output=None, success=False, error="project_id is required")

        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            return SkillResult(output=None, success=False, error=f"Project {project_id} not found")

        return SkillResult(
            output={
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "owner": project.owner,
                "priority": project.priority,
                "status": project.status,
                "progress": project.progress,
                "created_at": str(project.created_at) if project.created_at else None,
            },
            metadata={"action": "get"},
        )

    def _update_project(self, context: dict[str, Any], db) -> SkillResult:
        """更新项目。"""
        project_id = context.get("project_id")
        if not project_id:
            return SkillResult(output=None, success=False, error="project_id is required")

        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            return SkillResult(output=None, success=False, error=f"Project {project_id} not found")

        for field in ["name", "description", "owner", "priority", "status", "progress"]:
            if field in context:
                setattr(project, field, context[field])

        db.commit()
        db.refresh(project)
        logger.info("Updated project id=%d", project.id)
        return SkillResult(
            output={
                "id": project.id,
                "name": project.name,
                "status": project.status,
                "progress": project.progress,
            },
            metadata={"action": "update"},
        )

    def _delete_project(self, context: dict[str, Any], db) -> SkillResult:
        """删除项目。"""
        project_id = context.get("project_id")
        if not project_id:
            return SkillResult(output=None, success=False, error="project_id is required")

        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            return SkillResult(output=None, success=False, error=f"Project {project_id} not found")

        db.delete(project)
        db.commit()
        logger.info("Deleted project id=%d", project_id)
        return SkillResult(output={"deleted": True}, metadata={"action": "delete"})

    def _list_projects(self, context: dict[str, Any], db) -> SkillResult:
        """列出项目。"""
        status = context.get("status")
        query = db.query(ProjectModel)
        if status:
            query = query.filter(ProjectModel.status == status)

        projects = query.order_by(ProjectModel.id.desc()).all()
        return SkillResult(
            output=[
                {
                    "id": p.id,
                    "name": p.name,
                    "status": p.status,
                    "progress": p.progress,
                    "priority": p.priority,
                }
                for p in projects
            ],
            metadata={"action": "list", "count": len(projects)},
        )


class TaskAssignSkill(BaseSkill):
    """任务分配技能。

    将工作分配给指定 Agent，记录任务分配关系。
    """

    name = "task_assign"
    description = "Assign tasks to specialized agents"

    async def execute(self, context: dict[str, Any]) -> SkillResult:
        """执行任务分配。

        Args:
            context: 包含以下字段的字典：
                - project_id: 项目 ID
                - task: 任务描述
                - target_agent: 目标 Agent 名称
                - deadline: 截止日期（可选）
                - priority: 优先级（可选）

        Returns:
            SkillResult: 分配结果。
        """
        project_id = context.get("project_id")
        task = context.get("task", "")
        target_agent = context.get("target_agent", "")

        if not project_id:
            return SkillResult(output=None, success=False, error="project_id is required")
        if not task:
            return SkillResult(output=None, success=False, error="task is required")
        if not target_agent:
            return SkillResult(output=None, success=False, error="target_agent is required")

        assignment = {
            "project_id": project_id,
            "task": task,
            "target_agent": target_agent,
            "deadline": context.get("deadline"),
            "priority": context.get("priority", "medium"),
            "status": "assigned",
        }

        logger.info(
            "Assigned task to agent '%s' for project '%s': %s",
            target_agent,
            project_id,
            task,
        )

        return SkillResult(
            output=assignment,
            metadata={"action": "assign", "agent": target_agent},
        )


class ProgressTrackSkill(BaseSkill):
    """进度跟踪技能。

    监控项目整体进度，生成进度报告。
    """

    name = "progress_track"
    description = "Track project progress and generate status reports"

    async def execute(self, context: dict[str, Any]) -> SkillResult:
        """执行进度跟踪。

        Args:
            context: 包含以下字段的字典：
                - project_id: 项目 ID
                - include_tasks: 是否包含任务详情（可选，默认 True）

        Returns:
            SkillResult: 进度报告。
        """
        project_id = context.get("project_id")
        if not project_id:
            return SkillResult(output=None, success=False, error="project_id is required")

        db = next(get_db())
        try:
            project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
            if not project:
                return SkillResult(
                    output=None,
                    success=False,
                    error=f"Project {project_id} not found",
                )

            report = {
                "project_id": project_id,
                "project_name": project.name,
                "status": project.status,
                "progress": project.progress,
                "priority": project.priority,
                "owner": project.owner,
                "created_at": str(project.created_at) if project.created_at else None,
            }

            logger.info("Generated progress report for project '%s'", project_id)
            return SkillResult(output=report, metadata={"action": "track"})
        except Exception as exc:
            logger.exception("Progress track skill failed")
            return SkillResult(output=None, success=False, error=str(exc))
        finally:
            db.close()
