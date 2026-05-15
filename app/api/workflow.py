"""工作流 API 模块。

提供工作流的启动和状态查询接口。

主要端点：
    - POST /workflow/{project_id}/start: 启动工作流
    - GET /workflow/{project_id}/status: 获取工作流状态

使用示例：
    ```python
    from app.api.workflow import router
    app.include_router(router, prefix="/workflow")
    ```
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.state.models import get_db
from app.state.repository import StateRepository
from app.state.schemas import ProjectState

logger = logging.getLogger(__name__)
router = APIRouter()


class ErrorResponse(BaseModel):
    """错误响应模型。

    Attributes:
        detail: 错误详情。
    """
    detail: str


class StartWorkflowPayload(BaseModel):
    """启动工作流请求体。

    Attributes:
        context: 工作流上下文字典。
        initiated_by: 发起者标识。
        priority: 优先级，可选 low/normal/high/critical。
    """
    context: Dict[str, Any] = Field(default_factory=dict)
    initiated_by: str = Field(default="system", min_length=1)
    priority: str = Field(default="normal", pattern="^(low|normal|high|critical)$")


class StartWorkflowResponse(BaseModel):
    """启动工作流响应模型。

    Attributes:
        project_id: 项目 ID。
        status: 工作流状态。
    """
    project_id: str
    status: str


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应模型。

    Attributes:
        project_id: 项目 ID。
        status: 当前状态。
        updated_at: 最后更新时间 ISO 格式字符串。
    """
    project_id: str
    status: str
    updated_at: str | None


@router.post(
    "/{project_id}/start",
    response_model=StartWorkflowResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def start_workflow(
    project_id: str,
    payload: StartWorkflowPayload,
    db: Session = Depends(get_db),
):
    """启动指定项目的工作流。

    如果项目不存在则创建新项目状态。

    Args:
        project_id: 项目 ID。
        payload: 启动工作流请求体。
        db: 数据库会话，由依赖注入提供。

    Returns:
        StartWorkflowResponse: 启动结果。

    Raises:
        HTTPException: 操作失败时返回 500 错误。
    """
    try:
        repo = StateRepository(db)
        state = repo.get_state(project_id)
        if state is None:
            repo.update_state(
                project_id=project_id,
                state_json="{}",
                status="workflow_started",
            )
            logger.info("Started workflow for new project '%s' (by=%s, priority=%s)", project_id, payload.initiated_by, payload.priority)
        else:
            repo.update_state(
                project_id=project_id,
                state_json=state.state_json,
                status="workflow_started",
            )
            logger.info("Restarted workflow for existing project '%s' (by=%s, priority=%s)", project_id, payload.initiated_by, payload.priority)
        return {"project_id": project_id, "status": "workflow_started"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to start workflow for project '%s'", project_id)
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {exc}") from exc


@router.get(
    "/{project_id}/status",
    response_model=WorkflowStatusResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_workflow_status(
    project_id: str,
    db: Session = Depends(get_db),
):
    """获取指定项目的工作流状态。

    Args:
        project_id: 项目 ID。
        db: 数据库会话，由依赖注入提供。

    Returns:
        WorkflowStatusResponse: 工作流状态。

    Raises:
        HTTPException: 项目不存在返回 404，其他错误返回 500。
    """
    try:
        repo = StateRepository(db)
        state = repo.get_state(project_id)
        if state is None:
            logger.warning("Get workflow status failed: project '%s' not found", project_id)
            raise HTTPException(status_code=404, detail="Project not found")
        logger.debug("Retrieved workflow status for project '%s': %s", project_id, state.status)
        return {
            "project_id": project_id,
            "status": state.status,
            "updated_at": state.updated_at.isoformat() if state.updated_at else None,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get workflow status for project '%s'", project_id)
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {exc}") from exc
