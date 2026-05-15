"""工作流配置 API 模块。

提供工作流配置的 CRUD 管理接口，以及将 Vue Flow 图形配置
同步保存为 YAML 文件的功能。

主要端点：
    - GET /workflow-config/ - 列出所有工作流配置
    - GET /workflow-config/{id} - 获取单个工作流配置
    - POST /workflow-config/ - 创建工作流配置
    - PUT /workflow-config/{id} - 更新工作流配置
    - DELETE /workflow-config/{id} - 删除工作流配置
    - POST /workflow-config/{id}/sync-yaml - 同步保存为 YAML 文件

使用示例：
    ```python
    from app.api.workflow_config import router
    app.include_router(router, prefix="/workflow-config")
    ```
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.state.models import WorkflowConfigModel, get_db

logger = logging.getLogger(__name__)
router = APIRouter()

_WORKFLOW_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "config",
    "workflows",
)


class WorkflowConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    version: str = "1.0.0"
    flow_json: str = "{}"
    status: str = "draft"


class WorkflowConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    version: Optional[str] = None
    flow_json: Optional[str] = None
    status: Optional[str] = None


class WorkflowConfigResponse(BaseModel):
    id: int
    name: str
    description: str
    version: str
    flow_json: str
    yaml_path: Optional[str]
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SyncYamlResponse(BaseModel):
    success: bool
    yaml_path: str


def _model_to_response(model: WorkflowConfigModel) -> WorkflowConfigResponse:
    return WorkflowConfigResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        version=model.version,
        flow_json=model.flow_json,
        yaml_path=model.yaml_path,
        status=model.status,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _flow_json_to_pipeline(flow_json_str: str, name: str, version: str, description: str) -> Dict[str, Any]:
    """将 Vue Flow 的 nodes/edges JSON 转换为 workflow-pipeline.yaml 兼容格式。

    Args:
        flow_json_str: Vue Flow 的 JSON 字符串，包含 nodes 和 edges。
        name: 工作流名称。
        version: 版本号。
        description: 描述。

    Returns:
        Dict: 与 workflow-pipeline.yaml 格式兼容的字典。
    """
    try:
        flow = json.loads(flow_json_str)
    except json.JSONDecodeError:
        raise ValueError("Invalid flow_json: not valid JSON")

    nodes = flow.get("nodes", [])
    edges = flow.get("edges", [])

    node_map: Dict[str, Dict[str, Any]] = {}
    for node in nodes:
        node_id = node.get("id", "")
        data = node.get("data", {})
        node_map[node_id] = {
            "id": data.get("id", node_id),
            "name": data.get("name", node.get("label", node_id)),
            "agent": data.get("agent", ""),
            "activity": data.get("activity", data.get("id", node_id)),
            "requires_approval": data.get("requires_approval", True),
            "timeout_seconds": data.get("timeout_seconds", 300),
        }

    edge_map: Dict[str, List[str]] = {nid: [] for nid in node_map}
    in_degree: Dict[str, int] = {nid: 0 for nid in node_map}
    for edge in edges:
        source = edge.get("source", "")
        target = edge.get("target", "")
        if source in node_map and target in node_map:
            edge_map[source].append(target)
            in_degree[target] += 1

    ordered_ids: List[str] = []
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    while queue:
        queue.sort(key=lambda x: node_map[x].get("timeout_seconds", 300))
        current = queue.pop(0)
        ordered_ids.append(current)
        for neighbor in edge_map.get(current, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    for nid in node_map:
        if nid not in ordered_ids:
            ordered_ids.append(nid)

    stages = [node_map[nid] for nid in ordered_ids]

    return {
        "name": name,
        "version": version,
        "description": description,
        "stages": stages,
        "settings": {
            "default_timeout": 300,
            "max_retries": 3,
            "retry_delay": 5,
            "auto_rollback_on_failure": True,
        },
    }


@router.get("/", response_model=Dict[str, List[WorkflowConfigResponse]])
async def list_workflow_configs(db: Session = Depends(get_db)):
    try:
        configs = db.query(WorkflowConfigModel).order_by(WorkflowConfigModel.id.desc()).all()
        logger.info("Listed %d workflow configs", len(configs))
        return {"configs": [_model_to_response(c) for c in configs]}
    except Exception as exc:
        logger.exception("Failed to list workflow configs")
        raise HTTPException(status_code=500, detail=f"Failed to list workflow configs: {exc}") from exc


@router.get("/{config_id}", response_model=WorkflowConfigResponse)
async def get_workflow_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(WorkflowConfigModel).filter(WorkflowConfigModel.id == config_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail=f"Workflow config {config_id} not found")
    return _model_to_response(config)


@router.post("/", response_model=WorkflowConfigResponse, status_code=201)
async def create_workflow_config(payload: WorkflowConfigCreate, db: Session = Depends(get_db)):
    existing = db.query(WorkflowConfigModel).filter(WorkflowConfigModel.name == payload.name).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Workflow config with name '{payload.name}' already exists")
    try:
        config = WorkflowConfigModel(
            name=payload.name,
            description=payload.description,
            version=payload.version,
            flow_json=payload.flow_json,
            status=payload.status,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        logger.info("Created workflow config '%s' (id=%d)", config.name, config.id)
        return _model_to_response(config)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create workflow config '%s'", payload.name)
        raise HTTPException(status_code=500, detail=f"Failed to create workflow config: {exc}") from exc


@router.put("/{config_id}", response_model=WorkflowConfigResponse)
async def update_workflow_config(config_id: int, payload: WorkflowConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(WorkflowConfigModel).filter(WorkflowConfigModel.id == config_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail=f"Workflow config {config_id} not found")

    if payload.name is not None and payload.name != config.name:
        existing = db.query(WorkflowConfigModel).filter(WorkflowConfigModel.name == payload.name).first()
        if existing is not None:
            raise HTTPException(status_code=409, detail=f"Workflow config with name '{payload.name}' already exists")

    try:
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)
        db.commit()
        db.refresh(config)
        logger.info("Updated workflow config '%s' (id=%d)", config.name, config.id)
        return _model_to_response(config)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update workflow config %d", config_id)
        raise HTTPException(status_code=500, detail=f"Failed to update workflow config: {exc}") from exc


@router.delete("/{config_id}", response_model=Dict[str, bool])
async def delete_workflow_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(WorkflowConfigModel).filter(WorkflowConfigModel.id == config_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail=f"Workflow config {config_id} not found")
    try:
        db.delete(config)
        db.commit()
        logger.info("Deleted workflow config '%s' (id=%d)", config.name, config.id)
        return {"success": True}
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to delete workflow config %d", config_id)
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow config: {exc}") from exc


@router.post("/{config_id}/sync-yaml", response_model=SyncYamlResponse)
async def sync_yaml(config_id: int, db: Session = Depends(get_db)):
    config = db.query(WorkflowConfigModel).filter(WorkflowConfigModel.id == config_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail=f"Workflow config {config_id} not found")

    try:
        pipeline = _flow_json_to_pipeline(
            config.flow_json, config.name, config.version, config.description
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    os.makedirs(_WORKFLOW_DIR, exist_ok=True)

    safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in config.name)
    yaml_filename = f"{safe_name}.yaml"
    yaml_path = os.path.join(_WORKFLOW_DIR, yaml_filename)

    try:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(pipeline, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except OSError as exc:
        logger.exception("Failed to write YAML file '%s'", yaml_path)
        raise HTTPException(status_code=500, detail=f"Failed to write YAML file: {exc}") from exc

    try:
        config.yaml_path = yaml_path
        db.commit()
        db.refresh(config)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update yaml_path for config %d", config_id)
        raise HTTPException(status_code=500, detail=f"Failed to update yaml_path: {exc}") from exc

    logger.info("Synced workflow config '%s' to YAML: %s", config.name, yaml_path)
    return {"success": True, "yaml_path": yaml_path}
