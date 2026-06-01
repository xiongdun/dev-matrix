"""工作流 API 模块。

提供统一的 WorkflowEngine 封装，优先使用 Temporal 分布式执行，
当 Temporal 不可用时自动降级到 Pipeline 本地执行。

主要端点：
    - POST /workflow/{project_id}/start: 启动工作流（统一入口）
    - GET /workflow/{project_id}/status: 获取工作流状态

使用示例：
    ```python
    from app.api.workflow import router
    app.include_router(router, prefix="/workflow")
    ```
"""

import logging
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.schemas import ErrorResponse
from app.state.models import get_db
from app.state.repository import StateRepository
from app.workflow.engine import WorkflowEngine

logger = logging.getLogger(__name__)
router = APIRouter()


class StartWorkflowPayload(BaseModel):
    """启动工作流请求体。

    Attributes:
        context: 工作流上下文字典。
        initiated_by: 发起者标识。
        priority: 优先级，可选 low/normal/high/critical。
        flow_json: Vue Flow 的 JSON 图结构（可选）。
        template_id: 模板 ID（可选）。
    """

    context: dict[str, Any] = Field(default_factory=dict)
    initiated_by: str = Field(default="system", min_length=1)
    priority: str = Field(default="normal", pattern="^(low|normal|high|critical)$")
    flow_json: str = Field(default="")
    template_id: int = Field(default=0)


class StartWorkflowResponse(BaseModel):
    """启动工作流响应模型。

    Attributes:
        project_id: 项目 ID。
        status: 工作流状态。
        engine: 实际使用的引擎（temporal/pipeline）。
        workflow_id: Temporal 工作流 ID（仅 temporal 模式）。
    """

    project_id: str
    status: str
    engine: str = ""
    workflow_id: str = ""


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应模型。

    Attributes:
        project_id: 项目 ID。
        status: 当前状态。
        engine: 实际使用的引擎。
        updated_at: 最后更新时间 ISO 格式字符串。
    """

    project_id: str
    status: str
    engine: str = ""
    updated_at: str | None = None


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

    统一入口：优先使用 Temporal，不可用时降级到 Pipeline。

    Args:
        project_id: 项目 ID。
        payload: 启动工作流请求体。
        db: 数据库会话，由依赖注入提供。

    Returns:
        StartWorkflowResponse: 启动结果，包含实际使用的引擎信息。

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
            logger.info(
                "Started workflow for new project '%s' (by=%s, priority=%s)",
                project_id,
                payload.initiated_by,
                payload.priority,
            )
        else:
            state_json_val = cast(str, state.state_json)
            repo.update_state(
                project_id=project_id,
                state_json=state_json_val,
                status="workflow_started",
            )
            logger.info(
                "Restarted workflow for existing project '%s' (by=%s, priority=%s)",
                project_id,
                payload.initiated_by,
                payload.priority,
            )

        # 使用统一引擎启动工作流
        engine = WorkflowEngine()
        result = await engine.start_workflow(
            project_id=project_id,
            flow_json=payload.flow_json or None,
            context=payload.context,
            template_id=payload.template_id if payload.template_id > 0 else None,
        )

        return StartWorkflowResponse(
            project_id=project_id,
            status=result.get("status", "started"),
            engine=result.get("engine", ""),
            workflow_id=result.get("workflow_id", ""),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to start workflow for project '%s'", project_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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

    优先查询 Temporal，找不到则查询数据库。

    Args:
        project_id: 项目 ID。
        db: 数据库会话，由依赖注入提供。

    Returns:
        WorkflowStatusResponse: 工作流状态。

    Raises:
        HTTPException: 项目不存在返回 404，其他错误返回 500。
    """
    try:
        engine = WorkflowEngine()
        result = await engine.get_workflow_status(project_id)

        if result.get("status") == "not_found":
            logger.warning("Get workflow status failed: project '%s' not found", project_id)
            raise HTTPException(status_code=404, detail="Project not found")

        return WorkflowStatusResponse(
            project_id=project_id,
            status=result.get("status", "unknown"),
            engine=result.get("engine", ""),
            updated_at=result.get("updated_at"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to get workflow status for project '%s'", project_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
