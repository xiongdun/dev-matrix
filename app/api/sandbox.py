"""工具沙盒 API 模块。"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.sandbox.manager import SANDBOX_CONFIGS, SandboxConfig, ToolSandbox
from app.state.models import UserModel

logger = logging.getLogger(__name__)
router = APIRouter()


class ExecuteRequest(BaseModel):
    command: str
    cwd: str | None = None
    timeout: int | None = None
    sandbox_level: str = "standard"


class ReadFileRequest(BaseModel):
    path: str
    sandbox_level: str = "standard"


class WriteFileRequest(BaseModel):
    path: str
    content: str
    sandbox_level: str = "standard"


@router.post("/execute")
async def execute_command(
    payload: ExecuteRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """在沙盒中执行命令。"""
    config = SANDBOX_CONFIGS.get(payload.sandbox_level, SANDBOX_CONFIGS["standard"])
    sandbox = ToolSandbox(config)
    try:
        result = sandbox.execute(payload.command, cwd=payload.cwd, timeout=payload.timeout)
        return result
    finally:
        sandbox.cleanup()


@router.post("/read")
async def read_file(
    payload: ReadFileRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """在沙盒中读取文件。"""
    config = SANDBOX_CONFIGS.get(payload.sandbox_level, SANDBOX_CONFIGS["standard"])
    sandbox = ToolSandbox(config)
    try:
        return sandbox.read_file(payload.path)
    finally:
        sandbox.cleanup()


@router.post("/write")
async def write_file(
    payload: WriteFileRequest,
    current_user: UserModel = Depends(get_current_user),
):
    """在沙盒中写入文件。"""
    config = SANDBOX_CONFIGS.get(payload.sandbox_level, SANDBOX_CONFIGS["standard"])
    sandbox = ToolSandbox(config)
    try:
        return sandbox.write_file(payload.path, payload.content)
    finally:
        sandbox.cleanup()


@router.get("/configs")
async def list_configs(
    current_user: UserModel = Depends(get_current_user),
):
    """获取可用的沙盒配置。"""
    return {
        "configs": {
            name: {
                "read_only": config.read_only,
                "network_access": config.network_access,
                "max_execution_time": config.max_execution_time,
                "allowed_commands_count": len(config.allowed_commands) if config.allowed_commands else 0,
            }
            for name, config in SANDBOX_CONFIGS.items()
        }
    }
