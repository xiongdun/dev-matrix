"""统一工作流执行引擎模块。

提供 WorkflowEngine 类，完全基于 Temporal 工作流执行。

主要类:
    - WorkflowEngine: 统一工作流执行入口。

使用示例:
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

from temporalio.client import Client

from app.config import get_settings

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """统一工作流执行引擎。

    完全基于 Temporal 分布式执行。

    Attributes:
        _temporal_client: Temporal Client 实例（懒加载）。
    """

    def __init__(self):
        self._temporal_client: Optional[Client] = None

    async def _get_temporal_client(self) -> Client:
        """懒加载 Temporal Client。"""
        if self._temporal_client is not None:
            return self._temporal_client

        settings = get_settings()
        self._temporal_client = await Client.connect(settings.temporal_host)
        logger.info("Connected to Temporal server at %s", settings.temporal_host)
        return self._temporal_client

    async def start_workflow(
        self,
        project_id: str,
        flow_json: Optional[str] = None,
        stages: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None,
        template_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """启动工作流。

        Args:
            project_id: 项目 ID。
            flow_json: Vue Flow 的 JSON 图结构（优先使用）。
            stages: 阶段列表（flow_json 为空时使用）。
            context: 初始上下文。
            template_id: 模板 ID。

        Returns:
            执行结果字典，包含 status、project_id、workflow_id 等字段。
        """
        from app.workflow.definitions import DevWorkflow

        client = await self._get_temporal_client()
        workflow_id = f"dev-workflow-{project_id}"

        config: Dict[str, Any] = {
            "project_id": project_id,
            "context": context or {},
        }
        if flow_json:
            config["flow_json"] = flow_json
        elif stages:
            config["stages"] = stages
        if template_id:
            config["template_id"] = template_id

        await client.start_workflow(
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

        return {
            "status": "started",
            "project_id": project_id,
            "engine": "temporal",
            "workflow_id": workflow_id,
        }

    async def get_workflow_status(self, project_id: str) -> Dict[str, Any]:
        """获取工作流状态。

        查询 Temporal 工作流状态。

        Args:
            project_id: 项目 ID。

        Returns:
            状态字典。
        """
        client = await self._get_temporal_client()
        workflow_id = f"dev-workflow-{project_id}"
        handle = client.get_workflow_handle(workflow_id)

        try:
            description = await handle.describe()
            status = description.status
            status_name = (
                status.name
                if status is not None and hasattr(status, "name")
                else str(status)
            )
            return {
                "project_id": project_id,
                "status": status_name,
                "engine": "temporal",
                "workflow_id": workflow_id,
            }
        except Exception:
            # Temporal 中找不到，查询数据库
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
                "engine": "temporal",
                "updated_at": state.updated_at.isoformat() if state.updated_at else None,
            }
