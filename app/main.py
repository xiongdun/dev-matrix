from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.state.models import init_db
from app.api import requirements, approvals, workflow, registry
from app.skills.registry import _global_registry as skill_registry
from app.skills.base import BaseSkill
from app.core.registry.discovery import discover_and_register


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    discover_and_register("app.skills", skill_registry, BaseSkill)
    yield


app = FastAPI(
    title="DevMatrix",
    description="Multi-role Collaborative Software Development Agent Operating System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(requirements.router, prefix="/requirements", tags=["requirements"])
app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
app.include_router(workflow.router, prefix="/workflow", tags=["workflow"])
app.include_router(registry.router, prefix="/registry", tags=["registry"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
