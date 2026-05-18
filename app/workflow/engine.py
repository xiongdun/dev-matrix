"""统一工作流执行引擎模块。

提供 WorkflowEngine 类，统一封装 Temporal 和 Pipeline 两种执行后端。
优先使用 Temporal，当 Temporal 不可用时自动降级到 Pipeline 本地执行。

主要类：
    - WorkflowEngine: 统一工作流执行入口。

使用示例：
    ```python
    engine = WorkflowEngine()
    result = await engine.start_workflow(
        project_id="proj_1",
        flow_json='{"nodes": [...], "edges": [...]}',
        context={"requirement": "..."},
    )
    ```
"""

import logging
from typing import Any, Dict, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """统一工作流执行引擎。

    优先使用 Temporal 分布式执行，当 Temporal 不可用时自动降级到 Pipeline 本地执行。
    对调用方透明，无需关心底层使用的是哪个引擎。

    Attributes:
        temporal_available: Temporal 是否可用。
        _temporal_client: Temporal Client 实例（懒加载）。
    """

    def __init__(self):
        self.temporal_available = False
        self._temporal_client = None
        self._pipeline = None

    async def _get_temporal_client(self):
        """懒加载 Temporal Client。"""
        if self._temporal_client is not None:
            return self._temporal_client

        try:
            from temporalio.client import Client

            settings = get_settings()
            self._temporal_client = await Client.connect(settings.temporal_host)
            self.temporal_available = True
            logger.info("Connected to Temporal server at %s", settings.temporal_host)
        except Exception as exc:
            logger.warning(
                "Failed to connect to Temporal server: %s. "
                "Will fall back to Pipeline execution.",
                exc,
            )
            self.temporal_available = False
            self._temporal_client = None

        return self._temporal_client

    def _get_pipeline(self):
        """懒加载 Pipeline Executor。"""
        if self._pipeline is None:
            from app.workflow.pipeline.executor import WorkflowPipeline

            self._pipeline = WorkflowPipeline()
        return self._pipeline

    async def start_workflow(
        self,
        project_id: str,
        flow_json: Optional[str] = None,
        stages: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None,
        template_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """启动工作流。

        优先尝试使用 Temporal，如果 Temporal 不可用则降级到 Pipeline。

        Args:
            project_id: 项目 ID。
            flow_json: Vue Flow 的 JSON 图结构（优先使用）。
            stages: 阶段列表（flow_json 为空时使用）。
            context: 初始上下文。
            template_id: 模板 ID。

        Returns:
            执行结果字典，包含 status、project_id、engine 等字段。
        """
        # 先尝试 Temporal
        client = await self._get_temporal_client()
        if client is not None and self.temporal_available:
            try:
                return await self._start_with_temporal(
                    client, project_id, flow_json, stages, context
                )
            except Exception as exc:
                logger.warning(
                    "Temporal execution failed for project '%s': %s. "
                    "Falling back to Pipeline.",
                    project_id,
                    exc,
                )

        # 降级到 Pipeline
        return await self._start_with_pipeline(
            project_id, flow_json, stages, context, template_id
        )

    async def _start_with_temporal(
        self,
        client,
        project_id: str,
        flow_json: Optional[str],
        stages: Optional[list],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """使用 Temporal 启动工作流。"""
        from app.workflow.definitions import DevWorkflow

        workflow_id = f"dev-workflow-{project_id}"

        config = {
            "project_id": project_id,
            "context": context or {},
        }
        if flow_json:
            config["flow_json"] = flow_json
        elif stages:
            config["stages"] = stages

        handle = await client.start_workflow(
            DevWorkflow.run,
            args=[config],
            id=workflow_id,
            task_queue="devmatrix-task-queue",
        )

        logger.info(
            "Started Temporal workflow for project '%s' (workflow_id=%s)",
            project_id,
            workflow_id,
        )

        # handle 用于后续查询状态，当前保留引用
        _ = handle

        return {
            "status": "started",
            "project_id": project_id,
            "engine": "temporal",
            "workflow_id": workflow_id,
        }

    async def _start_with_pipeline(
        self,
        project_id: str,
        flow_json: Optional[str],
        stages: Optional[list],
        context: Optional[Dict[str, Any]],
        template_id: Optional[int],
    ) -> Dict[str, Any]:
        """使用 Pipeline 启动工作流（本地执行）。"""
        pipeline = self._get_pipeline()

        result = await pipeline.run(
            project_id=project_id,
            initial_context=context,
            template_id=template_id,
            flow_json=flow_json,
        )

        result["engine"] = "pipeline"

        logger.info(
            "Executed Pipeline workflow for project '%s' (status=%s)",
            project_id,
            result.get("status"),
        )

        return result

    async def get_workflow_status(self, project_id: str) -> Dict[str, Any]:
        """获取工作流状态。

        优先查询 Temporal，如果找不到则查询数据库。

        Args:
            project_id: 项目 ID。

        Returns:
            状态字典。
        """
        # 先尝试 Temporal
        client = await self._get_temporal_client()
        if client is not None and self.temporal_available:
            try:

                workflow_id = f"dev-workflow-{project_id}"
                handle = client.get_workflow_handle(workflow_id)
                description = await handle.describe()

                status_name = (
                    description.status.name
                    if hasattr(description.status, "name")
                    else str(description.status)
                )

                return {
                    "project_id": project_id,
                    "status": status_name,
                    "engine": "temporal",
                    "workflow_id": workflow_id,
                }
            except Exception:
                # Temporal 中找不到，继续查数据库
                pass

        # 查询数据库
        from app.state.models import get_db
        from app.state.repository import StateRepository

        db = next(get_db())
        repo = StateRepository(db)
        state = repo.get_state(project_id)

        if state is None:
            return {
                "project_id": project_id,
                "status": "not_found",
                "engine": "unknown",
            }

        return {
            "project_id": project_id,
            "status": state.status,
            "engine": "pipeline",
            "updated_at": state.updated_at.isoformat() if state.updated_at else None,
        }
