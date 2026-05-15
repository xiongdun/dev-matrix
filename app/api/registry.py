"""注册表 API 模块。

提供 Agent、Skill 和 LLM Provider 的注册表管理接口，
包括列表查询、技能挂载/卸载、技能上传等功能。

主要端点：
    - GET /registry/agents: 列出所有已注册的 Agent
    - GET /registry/agents/detail: 列出 Agent 详细信息
    - POST /registry/agents/{agent_name}/skills/{skill_name}: 挂载技能
    - DELETE /registry/agents/{agent_name}/skills/{skill_name}: 卸载技能
    - GET /registry/skills: 列出所有已注册的技能
    - POST /registry/skills/upload: 上传自定义技能
    - GET /registry/llm-providers: 列出 LLM 提供商

使用示例：
    ```python
    from app.api.registry import router
    app.include_router(router, prefix="/registry")
    ```
"""

import logging
import os
import re
import sys
import importlib.util
from typing import Dict, List, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.registry.agent_registry import agent_registry
from app.core.registry.llm_registry import llm_registry
from app.skills.registry import _global_registry as skill_registry
from app.skills.base import BaseSkill, SkillConfig
from app.llm.router import LLMRouter
from app.state.repository import StateRepository
from app.state.models import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# 内存中的 Agent 实例存储和状态跟踪
_agent_instances: Dict[str, Any] = {}
_agent_status: Dict[str, str] = {}


class AgentInfoResponse(BaseModel):
    """Agent 基本信息响应模型。

    Attributes:
        name: Agent 名称。
        description: Agent 描述。
    """
    name: str
    description: str


class AgentDetailResponse(AgentInfoResponse):
    """Agent 详细信息响应模型。

    Attributes:
        name: Agent 名称。
        description: Agent 描述。
        status: Agent 当前状态。
        skills: 已挂载的技能列表。
    """
    status: str
    skills: List[str]


class SkillInfoResponse(BaseModel):
    """技能信息响应模型。

    Attributes:
        name: 技能名称。
        description: 技能描述。
        used_by: 使用该技能的 Agent 列表。
    """
    name: str
    description: str
    used_by: List[str] = []


class SkillUploadPayload(BaseModel):
    """技能上传请求体模型。

    Attributes:
        name: 技能名称，长度 1-128 字符。
        description: 技能描述，至少 1 个字符。
        code: 技能代码字符串，至少 1 个字符。
        config: 技能配置字典，可选。
    """
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    config: Dict[str, Any] = {}


class SkillUploadResponse(BaseModel):
    """技能上传响应模型。

    Attributes:
        success: 是否上传成功。
        name: 上传的技能名称。
        description: 上传的技能描述。
    """
    success: bool
    name: str
    description: str


class MountSkillResponse(BaseModel):
    """技能挂载/卸载响应模型。

    Attributes:
        success: 操作是否成功。
        agent: Agent 名称。
        skill: 技能名称。
    """
    success: bool
    agent: str
    skill: str


class ProviderResponse(BaseModel):
    """LLM 提供商响应模型。

    Attributes:
        name: 提供商名称。
        description: 提供商描述。
    """
    name: str
    description: str


class ErrorResponse(BaseModel):
    """错误响应模型。

    Attributes:
        detail: 错误详情。
    """
    detail: str


def _get_or_create_agent(agent_name: str) -> Any:
    """获取或创建 Agent 实例用于技能组合。

    如果 Agent 已存在则返回缓存实例，否则创建新实例并缓存。

    Args:
        agent_name: Agent 注册名称。

    Returns:
        Any: Agent 实例。

    Raises:
        HTTPException: 数据库连接失败时返回 503 错误。
    """
    if agent_name in _agent_instances:
        return _agent_instances[agent_name]

    agent_cls = agent_registry.get(agent_name)
    try:
        db = next(get_db())
    except Exception as exc:
        logger.exception("Database connection failed when creating agent '%s'", agent_name)
        raise HTTPException(status_code=503, detail=f"Database connection failed: {exc}") from exc
    llm_router = LLMRouter()
    state_repo = StateRepository(db)
    agent = agent_cls(llm_router=llm_router, state_repository=state_repo)
    _agent_instances[agent_name] = agent
    if agent_name not in _agent_status:
        _agent_status[agent_name] = "idle"
    return agent


@router.get("/agents", response_model=Dict[str, List[AgentInfoResponse]])
async def list_agents() -> Dict[str, List[AgentInfoResponse]]:
    """列出所有已注册的 Agent。

    Returns:
        Dict: 包含 Agent 列表的字典。

    Raises:
        HTTPException: 查询失败时返回 500 错误。
    """
    try:
        agents = [
            {"name": name, "description": cls.description}
            for name, cls in agent_registry.list().items()
        ]
        logger.info("Listed %d agents", len(agents))
        return {"agents": agents}
    except Exception as exc:
        logger.exception("Failed to list agents")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {exc}") from exc


@router.get("/agents/detail", response_model=Dict[str, List[AgentDetailResponse]])
async def list_agent_details() -> Dict[str, List[AgentDetailResponse]]:
    """列出所有 Agent 的详细信息，包括状态和已挂载技能。

    Returns:
        Dict: 包含 Agent 详细信息的字典。

    Raises:
        HTTPException: 查询失败时返回 500 错误。
    """
    try:
        agents: List[Dict[str, Any]] = []
        for name, cls in agent_registry.list().items():
            try:
                agent = _get_or_create_agent(name)
                agents.append({
                    "name": name,
                    "description": cls.description,
                    "status": _agent_status.get(name, "idle"),
                    "skills": agent.list_skills(),
                })
            except HTTPException:
                raise
            except Exception as exc:
                logger.error("Failed to get details for agent '%s': %s", name, exc)
                agents.append({
                    "name": name,
                    "description": cls.description,
                    "status": "error",
                    "skills": [],
                })
        logger.info("Listed details for %d agents", len(agents))
        return {"agents": agents}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to list agent details")
        raise HTTPException(status_code=500, detail=f"Failed to list agent details: {exc}") from exc


@router.post(
    "/agents/{agent_name}/skills/{skill_name}",
    response_model=MountSkillResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def mount_skill(agent_name: str, skill_name: str) -> MountSkillResponse:
    """为指定 Agent 挂载技能。

    Args:
        agent_name: Agent 名称。
        skill_name: 技能名称。

    Returns:
        MountSkillResponse: 挂载结果。

    Raises:
        HTTPException: Agent 或 Skill 不存在返回 404，已挂载返回 409。
    """
    try:
        agent = _get_or_create_agent(agent_name)
    except HTTPException:
        raise
    except KeyError:
        logger.warning("Mount skill failed: agent '%s' not found", agent_name)
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    except Exception as exc:
        logger.exception("Unexpected error getting agent '%s'", agent_name)
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc

    try:
        skill_cls = skill_registry.get(skill_name)
    except KeyError:
        logger.warning("Mount skill failed: skill '%s' not found", skill_name)
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")
    except Exception as exc:
        logger.exception("Unexpected error getting skill '%s'", skill_name)
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc

    if agent.has_skill(skill_name):
        logger.warning(
            "Skill '%s' is already mounted on agent '%s'", skill_name, agent_name
        )
        raise HTTPException(
            status_code=409,
            detail=f"Skill '{skill_name}' is already mounted on agent '{agent_name}'",
        )

    try:
        skill = skill_cls()
        agent.use_skill(skill)
    except Exception as exc:
        logger.exception("Failed to mount skill '%s' on agent '%s'", skill_name, agent_name)
        raise HTTPException(status_code=500, detail=f"Failed to mount skill: {exc}") from exc

    logger.info("Mounted skill '%s' on agent '%s'", skill_name, agent_name)
    return {"success": True, "agent": agent_name, "skill": skill_name}


@router.delete(
    "/agents/{agent_name}/skills/{skill_name}",
    response_model=MountSkillResponse,
    responses={404: {"model": ErrorResponse}},
)
async def unmount_skill(agent_name: str, skill_name: str) -> MountSkillResponse:
    """从指定 Agent 卸载技能。

    Args:
        agent_name: Agent 名称。
        skill_name: 技能名称。

    Returns:
        MountSkillResponse: 卸载结果。

    Raises:
        HTTPException: Agent 不存在或技能未挂载返回 404。
    """
    try:
        agent = _get_or_create_agent(agent_name)
    except HTTPException:
        raise
    except KeyError:
        logger.warning("Unmount skill failed: agent '%s' not found", agent_name)
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    except Exception as exc:
        logger.exception("Unexpected error getting agent '%s'", agent_name)
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}") from exc

    if not agent.has_skill(skill_name):
        logger.warning(
            "Unmount skill failed: skill '%s' not mounted on agent '%s'", skill_name, agent_name
        )
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_name}' not mounted on agent '{agent_name}'",
        )

    try:
        del agent._skills[skill_name]
    except Exception as exc:
        logger.exception("Failed to unmount skill '%s' from agent '%s'", skill_name, agent_name)
        raise HTTPException(status_code=500, detail=f"Failed to unmount skill: {exc}") from exc

    logger.info("Unmounted skill '%s' from agent '%s'", skill_name, agent_name)
    return {"success": True, "agent": agent_name, "skill": skill_name}


@router.get("/skills", response_model=Dict[str, List[SkillInfoResponse]])
async def list_skills() -> Dict[str, List[SkillInfoResponse]]:
    """列出所有已注册的技能及其使用情况。

    Returns:
        Dict: 包含技能列表和使用者信息的字典。

    Raises:
        HTTPException: 查询失败时返回 500 错误。
    """
    try:
        skills = [
            {"name": name, "description": cls.description}
            for name, cls in skill_registry.list().items()
        ]
        skill_to_agents: Dict[str, List[str]] = {s["name"]: [] for s in skills}
        for agent_name, _ in agent_registry.list().items():
            try:
                agent = _get_or_create_agent(agent_name)
                for sk_name in agent.list_skills():
                    if sk_name in skill_to_agents:
                        skill_to_agents[sk_name].append(agent_name)
            except Exception as exc:
                logger.error("Failed to list skills for agent '%s': %s", agent_name, exc)

        for s in skills:
            s["used_by"] = skill_to_agents.get(s["name"], [])

        logger.info("Listed %d skills", len(skills))
        return {"skills": skills}
    except Exception as exc:
        logger.exception("Failed to list skills")
        raise HTTPException(status_code=500, detail=f"Failed to list skills: {exc}") from exc


# 上传技能代码中禁止包含的危险导入/模式
_FORBIDDEN_PATTERNS = [
    r"\bos\.system\b",
    r"\bsubprocess\.\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bcompile\s*\(",
    r"\b__import__\s*\(",
    r"\bimportlib\.import_module\b",
    r"\bopen\s*\(",
    r"\binput\s*\(",
    r"\bfile\s*\(",
    r"\bpty\.\b",
    r"\bcommands\.\b",
    r"\bpopen\b",
    r"\bspawn\b",
    r"\bos\.popen\b",
    r"\bos\.spawn\b",
    r"\bos\.execl\b",
    r"\bos\.execv\b",
    r"\bos\.execve\b",
    r"\bos\.kill\b",
    r"\bos\.remove\b",
    r"\bos\.rmdir\b",
    r"\bos\.unlink\b",
    r"\bshutil\.rmtree\b",
    r"\bshutil\.move\b",
    r"\bctypes\.\b",
    r"\bmmap\.\b",
    r"\bpickle\.loads?\b",
    r"\byaml\.load\b",
    r"\byaml\.unsafe_load\b",
]


def _validate_skill_code(code: str) -> None:
    """验证上传的技能代码是否包含危险模式。

    Args:
        code: 要验证的技能代码字符串。

    Raises:
        HTTPException: 发现危险模式时返回 400 错误。
    """
    for pattern in _FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            logger.warning("Skill code contains forbidden pattern: %s", pattern)
            raise HTTPException(
                status_code=400,
                detail=f"Skill code contains forbidden pattern: {pattern}",
            )


@router.post(
    "/skills/upload",
    response_model=SkillUploadResponse,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def upload_skill(payload: SkillUploadPayload) -> SkillUploadResponse:
    """上传并注册自定义技能。

    验证代码安全性，保存到文件系统，动态导入并注册到技能注册表。

    Args:
        payload: 技能上传请求体。

    Returns:
        SkillUploadResponse: 上传结果。

    Raises:
        HTTPException: 验证失败 400，已存在 409，处理失败 500。
    """
    _validate_skill_code(payload.code)

    custom_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills", "custom")
    os.makedirs(custom_dir, exist_ok=True)

    file_path = os.path.join(custom_dir, f"{payload.name}.py")
    if os.path.exists(file_path):
        logger.warning("Upload skill failed: skill '%s' already exists", payload.name)
        raise HTTPException(status_code=409, detail=f"Skill '{payload.name}' already exists")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(payload.code)
    except OSError as exc:
        logger.exception("Failed to write skill file '%s'", file_path)
        raise HTTPException(status_code=500, detail=f"Failed to write skill file: {exc}") from exc

    try:
        module_name = f"app.skills.custom.{payload.name}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            logger.error("Failed to load skill module spec for '%s'", payload.name)
            os.remove(file_path)
            raise HTTPException(status_code=500, detail="Failed to load skill module")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        skill_cls = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseSkill) and attr is not BaseSkill:
                skill_cls = attr
                break

        if skill_cls is None:
            logger.warning("No class extending BaseSkill found in uploaded code for '%s'", payload.name)
            os.remove(file_path)
            del sys.modules[module_name]
            raise HTTPException(
                status_code=400,
                detail="No class extending BaseSkill found in uploaded code",
            )

        skill_cls.name = payload.name
        skill_cls.description = payload.description
        skill_registry.register(payload.name, skill_cls)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to process uploaded skill '%s'", payload.name)
        if os.path.exists(file_path):
            os.remove(file_path)
        if f"app.skills.custom.{payload.name}" in sys.modules:
            del sys.modules[f"app.skills.custom.{payload.name}"]
        raise HTTPException(status_code=500, detail=f"Failed to process skill: {exc}") from exc

    logger.info("Uploaded and registered skill '%s'", payload.name)
    return {"success": True, "name": payload.name, "description": payload.description}


@router.get("/llm-providers", response_model=Dict[str, List[ProviderResponse]])
async def list_llm_providers() -> Dict[str, List[ProviderResponse]]:
    """列出所有已注册的 LLM 提供商。

    Returns:
        Dict: 包含提供商列表的字典。

    Raises:
        HTTPException: 查询失败时返回 500 错误。
    """
    try:
        providers = [
            {"name": name, "description": cls.name}
            for name, cls in llm_registry.list().items()
        ]
        logger.info("Listed %d LLM providers", len(providers))
        return {"providers": providers}
    except Exception as exc:
        logger.exception("Failed to list LLM providers")
        raise HTTPException(status_code=500, detail=f"Failed to list LLM providers: {exc}") from exc
