import os
import sys
import importlib.util
from typing import Dict, List, Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.core.registry.agent_registry import agent_registry
from app.core.registry.llm_registry import llm_registry
from app.skills.registry import _global_registry as skill_registry
from app.skills.base import BaseSkill, SkillConfig
from app.llm.router import LLMRouter
from app.state.repository import StateRepository
from app.state.models import get_db

router = APIRouter()

# In-memory agent instance store and status tracking
_agent_instances: Dict[str, Any] = {}
_agent_status: Dict[str, str] = {}


def _get_or_create_agent(agent_name: str):
    """Get or create an agent instance for skill composition."""
    if agent_name in _agent_instances:
        return _agent_instances[agent_name]

    agent_cls = agent_registry.get(agent_name)
    db = next(get_db())
    llm_router = LLMRouter()
    state_repo = StateRepository(db)
    agent = agent_cls(llm_router=llm_router, state_repository=state_repo)
    _agent_instances[agent_name] = agent
    if agent_name not in _agent_status:
        _agent_status[agent_name] = "idle"
    return agent


@router.get("/agents")
async def list_agents():
    agents = [
        {"name": name, "description": cls.description}
        for name, cls in agent_registry.list().items()
    ]
    return {"agents": agents}


@router.get("/agents/detail")
async def list_agent_details():
    agents = []
    for name, cls in agent_registry.list().items():
        agent = _get_or_create_agent(name)
        agents.append({
            "name": name,
            "description": cls.description,
            "status": _agent_status.get(name, "idle"),
            "skills": agent.list_skills(),
        })
    return {"agents": agents}


@router.post("/agents/{agent_name}/skills/{skill_name}")
async def mount_skill(agent_name: str, skill_name: str):
    try:
        agent = _get_or_create_agent(agent_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    try:
        skill_cls = skill_registry.get(skill_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    skill = skill_cls()
    agent.use_skill(skill)
    return {"success": True, "agent": agent_name, "skill": skill_name}


@router.delete("/agents/{agent_name}/skills/{skill_name}")
async def unmount_skill(agent_name: str, skill_name: str):
    try:
        agent = _get_or_create_agent(agent_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    if not agent.has_skill(skill_name):
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not mounted on agent '{agent_name}'")

    del agent._skills[skill_name]
    return {"success": True, "agent": agent_name, "skill": skill_name}


@router.get("/skills")
async def list_skills():
    skills = [
        {"name": name, "description": cls.description}
        for name, cls in skill_registry.list().items()
    ]
    # Reverse map: which agents use each skill
    skill_to_agents: Dict[str, List[str]] = {s["name"]: [] for s in skills}
    for agent_name, _ in agent_registry.list().items():
        agent = _get_or_create_agent(agent_name)
        for skill_name in agent.list_skills():
            if skill_name in skill_to_agents:
                skill_to_agents[skill_name].append(agent_name)

    for s in skills:
        s["used_by"] = skill_to_agents.get(s["name"], [])

    return {"skills": skills}


class SkillUploadPayload(BaseModel):
    name: str
    description: str
    code: str
    config: Dict[str, Any] = {}


@router.post("/skills/upload")
async def upload_skill(payload: SkillUploadPayload):
    custom_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills", "custom")
    os.makedirs(custom_dir, exist_ok=True)

    file_path = os.path.join(custom_dir, f"{payload.name}.py")
    if os.path.exists(file_path):
        raise HTTPException(status_code=409, detail=f"Skill '{payload.name}' already exists")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(payload.code)

    # Dynamic import and register
    module_name = f"app.skills.custom.{payload.name}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise HTTPException(status_code=500, detail="Failed to load skill module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Find the skill class inheriting BaseSkill
    skill_cls = None
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, BaseSkill) and attr is not BaseSkill:
            skill_cls = attr
            break

    if skill_cls is None:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="No class extending BaseSkill found in uploaded code")

    skill_cls.name = payload.name
    skill_cls.description = payload.description
    skill_registry.register(payload.name, skill_cls)

    return {"success": True, "name": payload.name, "description": payload.description}


@router.get("/llm-providers")
async def list_llm_providers():
    providers = [
        {"name": name, "description": cls.name}
        for name, cls in llm_registry.list().items()
    ]
    return {"providers": providers}
