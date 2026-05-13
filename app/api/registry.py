from fastapi import APIRouter

from app.core.registry.agent_registry import agent_registry
from app.core.registry.llm_registry import llm_registry

router = APIRouter()


@router.get("/agents")
async def list_agents():
    agents = [
        {"name": name, "description": cls.description}
        for name, cls in agent_registry.list().items()
    ]
    return {"agents": agents}


@router.get("/llm-providers")
async def list_llm_providers():
    providers = [
        {"name": name, "description": cls.name}
        for name, cls in llm_registry.list().items()
    ]
    return {"providers": providers}
