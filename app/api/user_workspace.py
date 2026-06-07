"""用户 Workspace API 模块。

提供指定用户的完整 workspace 数据读取接口。
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.memory.manager import (
    UserMemoryManager,
    get_all_plugins,
    get_collaboration_config,
    get_soul_prompt,
    get_user_artifacts,
    get_user_hooks,
    get_user_mcp_servers,
    get_user_rules,
    get_user_skills,
    get_user_templates,
)
from app.state.models import UserModel

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{user_id}/workspace")
async def get_user_workspace(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的完整 workspace 数据。"""
    mgr = UserMemoryManager(user_id)

    if not mgr.user_dir.exists():
        raise HTTPException(status_code=404, detail=f"User {user_id} workspace not found")

    result: dict[str, Any] = {
        "user_id": user_id,
        "profile": mgr.get_profile(),
        "memories": mgr.get_memories(),
        "soul": get_soul_prompt(user_id),
        "skills": get_user_skills(user_id),
        "mcp_servers": get_user_mcp_servers(user_id),
        "rules": get_user_rules(user_id),
        "templates": get_user_templates(user_id),
        "hooks": get_user_hooks(user_id),
        "plugins": get_all_plugins(user_id),
        "artifacts": get_user_artifacts(user_id),
        "collaboration": get_collaboration_config(user_id),
        "projects": {},
    }

    if mgr.projects_dir.exists():
        for md_file in sorted(mgr.projects_dir.glob("*.md")):
            project_id = md_file.stem
            result["projects"][project_id] = mgr.get_project_memory(project_id)

    return result


@router.get("/{user_id}/workspace/soul")
async def get_user_soul(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的 soul.md 内容。"""
    mgr = UserMemoryManager(user_id)
    soul_path = mgr.user_dir / "soul.md"
    if not soul_path.exists():
        return {"soul": ""}
    return {"soul": soul_path.read_text(encoding="utf-8")}


@router.get("/{user_id}/workspace/memory")
async def get_user_memory(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的 memory.md 内容。"""
    mgr = UserMemoryManager(user_id)
    return {
        "memories": mgr.get_memories(),
        "profile": mgr.get_profile(),
    }


@router.get("/{user_id}/workspace/skills")
async def get_user_skills_list(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的技能列表。"""
    return {"skills": get_user_skills(user_id)}


@router.get("/{user_id}/workspace/mcp")
async def get_user_mcp(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的 MCP 服务器配置。"""
    return {"mcp_servers": get_user_mcp_servers(user_id)}


@router.get("/{user_id}/workspace/projects")
async def get_user_projects(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的所有项目记忆。"""
    mgr = UserMemoryManager(user_id)
    projects = {}
    if mgr.projects_dir.exists():
        for md_file in sorted(mgr.projects_dir.glob("*.md")):
            project_id = md_file.stem
            projects[project_id] = mgr.get_project_memory(project_id)
    return {"projects": projects}


@router.get("/{user_id}/workspace/rules")
async def get_user_rules_list(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的规则列表。"""
    return {"rules": get_user_rules(user_id)}


@router.get("/{user_id}/workspace/templates")
async def get_user_templates_list(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的模板列表。"""
    return {"templates": get_user_templates(user_id)}


@router.get("/{user_id}/workspace/hooks")
async def get_user_hooks_list(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的钩子列表。"""
    return {"hooks": get_user_hooks(user_id)}


@router.get("/{user_id}/workspace/plugins")
async def get_user_plugins_list(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的插件列表（含共享插件）。"""
    return {"plugins": get_all_plugins(user_id)}


@router.get("/{user_id}/workspace/artifacts")
async def get_user_artifacts_list(
    user_id: int,
    project_id: str | None = None,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的产出物。"""
    return {"artifacts": get_user_artifacts(user_id, project_id)}


@router.get("/{user_id}/workspace/collaboration")
async def get_user_collaboration(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
):
    """获取指定用户的协作配置。"""
    return {"collaboration": get_collaboration_config(user_id)}
