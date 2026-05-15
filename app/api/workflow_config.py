"""工作流配置/模板 API 模块。

提供工作流配置的 CRUD 管理接口、模板管理接口，
以及将 Vue Flow 图形配置同步保存为 YAML 文件的功能。

主要端点：
    - GET /workflow-config/ - 列出所有工作流配置
    - GET /workflow-config/templates - 列出所有预置模板
    - GET /workflow-config/{id} - 获取单个工作流配置
    - POST /workflow-config/ - 创建工作流配置
    - POST /workflow-config/{id}/instantiate - 从模板创建实例
    - PUT /workflow-config/{id} - 更新工作流配置
    - DELETE /workflow-config/{id} - 删除工作流配置
    - POST /workflow-config/{id}/sync-yaml - 同步保存为 YAML 文件
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

from app.state.models import WorkflowConfigModel, WorkflowInstanceModel, get_db

logger = logging.getLogger(__name__)
router = APIRouter()

_WORKFLOW_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "config",
    "workflows",
)

PRESET_TEMPLATES = [
    {"name": "standard-dev-flow", "category": "standard",
     "description": "Standard development workflow with full human approval checkpoints"},
    {"name": "hotfix-flow", "category": "hotfix",
     "description": "Emergency hotfix workflow with minimal approval steps for rapid deployment"},
    {"name": "db-change-flow", "category": "db_change",
     "description": "Database change workflow with mandatory architecture review and dual approval"},
    {"name": "auto-fix-flow", "category": "auto_fix",
     "description": "Automated fix workflow for lint/type errors with auto-approval"},
]


class WorkflowConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    version: str = "1.0.0"
    flow_json: str = Field(default="{}", max_length=1048576)
    status: str = "draft"


class WorkflowConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    version: Optional[str] = None
    flow_json: Optional[str] = Field(None, max_length=1048576)
    status: Optional[str] = None


class WorkflowConfigResponse(BaseModel):
    id: int
    name: str
    description: str
    version: str
    flow_json: str
    yaml_path: Optional[str]
    status: str
    is_template: bool = False
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SyncYamlResponse(BaseModel):
    success: bool
    yaml_path: str


class InstantiateRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=64)


class WorkflowInstanceResponse(BaseModel):
    id: int
    instance_id: str
    template_id: Optional[int]
    project_id: str
    current_state: str
    participants: List[str] = []
    artifacts: List[Dict[str, Any]] = []
    status: str
    context_json: str = "{}"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def _model_to_response(model: WorkflowConfigModel) -> WorkflowConfigResponse:
    return WorkflowConfigResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        version=model.version,
        flow_json=model.flow_json,
        yaml_path=model.yaml_path,
        status=model.status,
        is_template=bool(model.is_template),
        category=model.category,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _instance_to_response(model: WorkflowInstanceModel) -> WorkflowInstanceResponse:
    participants = json.loads(model.participants) if model.participants else []
    artifacts = json.loads(model.artifacts) if model.artifacts else []
    return WorkflowInstanceResponse(
        id=model.id,
        instance_id=model.instance_id,
        template_id=model.template_id,
        project_id=model.project_id,
        current_state=model.current_state,
        participants=participants,
        artifacts=artifacts,
        status=model.status,
        context_json=model.context_json,
        started_at=model.started_at,
        completed_at=model.completed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _generate_instance_id(db: Session) -> str:
    year = datetime.utcnow().year
    prefix = f"WF-{year}-"
    last = db.query(WorkflowInstanceModel).filter(
        WorkflowInstanceModel.instance_id.like(f"{prefix}%")
    ).order_by(WorkflowInstanceModel.id.desc()).first()
    seq = 1
    if last and last.instance_id.startswith(prefix):
        try:
            seq = int(last.instance_id[len(prefix):]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:03d}"


def _extract_participants(flow_json_str: str) -> List[str]:
    try:
        flow = json.loads(flow_json_str)
    except (json.JSONDecodeError, TypeError):
        return []
    agents = set()
    for node in flow.get("nodes", []):
        data = node.get("data", {})
        agent = data.get("agent", "")
        if agent:
            agents.add(agent)
    return sorted(agents)


def seed_templates(db: Session) -> None:
    """将预置模板 YAML 文件同步到数据库（幂等）。"""
    for tpl_info in PRESET_TEMPLATES:
        existing = db.query(WorkflowConfigModel).filter(
            WorkflowConfigModel.name == tpl_info["name"]
        ).first()
        if existing is not None:
            continue

        yaml_path = os.path.join(_WORKFLOW_DIR, f"{tpl_info['name']}.yaml")
        flow_json = "{}"
        if os.path.exists(yaml_path):
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    pipeline_data = yaml.safe_load(f)
                stages = pipeline_data.get("stages", [])
                nodes = []
                edges = []
                for i, s in enumerate(stages):
                    nodes.append({
                        "id": s["id"],
                        "type": "agentNode",
                        "position": {"x": 250, "y": i * 120},
                        "data": {
                            "id": s["id"],
                            "name": s.get("name", s["id"]),
                            "agent": s.get("agent", ""),
                            "activity": s.get("activity", s["id"]),
                            "requires_approval": s.get("requires_approval", True),
                            "timeout_seconds": s.get("timeout_seconds", 300),
                        },
                    })
                    if i > 0:
                        edges.append({
                            "id": f"e-{stages[i-1]['id']}-{s['id']}",
                            "source": stages[i - 1]["id"],
                            "target": s["id"],
                        })
                flow_json = json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False)
            except Exception:
                logger.exception("Failed to load template YAML: %s", yaml_path)

        config = WorkflowConfigModel(
            name=tpl_info["name"],
            description=tpl_info["description"],
            version="1.0.0",
            flow_json=flow_json,
            yaml_path=yaml_path if os.path.exists(yaml_path) else None,
            status="active",
            is_template=1,
            category=tpl_info["category"],
        )
        db.add(config)

    try:
        db.commit()
        logger.info("Template seeding completed")
    except Exception:
        db.rollback()
        logger.exception("Template seeding failed")


def _flow_json_to_pipeline(flow_json_str: str, name: str, version: str, description: str) -> Dict[str, Any]:
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


@router.get("/templates", response_model=Dict[str, List[WorkflowConfigResponse]])
async def list_templates(db: Session = Depends(get_db)):
    try:
        templates = db.query(WorkflowConfigModel).filter(
            WorkflowConfigModel.is_template == 1
        ).order_by(WorkflowConfigModel.id.asc()).all()
        logger.info("Listed %d workflow templates", len(templates))
        return {"templates": [_model_to_response(t) for t in templates]}
    except Exception as exc:
        logger.exception("Failed to list workflow templates")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/", response_model=Dict[str, List[WorkflowConfigResponse]])
async def list_workflow_configs(db: Session = Depends(get_db)):
    try:
        configs = db.query(WorkflowConfigModel).order_by(WorkflowConfigModel.id.desc()).all()
        logger.info("Listed %d workflow configs", len(configs))
        return {"workflows": [_model_to_response(c) for c in configs]}
    except Exception as exc:
        logger.exception("Failed to list workflow configs")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/{config_id}/instantiate", response_model=WorkflowInstanceResponse, status_code=201)
async def instantiate_template(config_id: int, payload: InstantiateRequest, db: Session = Depends(get_db)):
    config = db.query(WorkflowConfigModel).filter(WorkflowConfigModel.id == config_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail=f"Workflow config {config_id} not found")

    existing = db.query(WorkflowInstanceModel).filter(
        WorkflowInstanceModel.project_id == payload.project_id,
        WorkflowInstanceModel.status.in_(["running", "paused"]),
    ).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Project '{payload.project_id}' already has an active instance ({existing.instance_id})")

    participants = _extract_participants(config.flow_json)
    instance_id = _generate_instance_id(db)

    try:
        instance = WorkflowInstanceModel(
            instance_id=instance_id,
            template_id=config.id,
            project_id=payload.project_id,
            current_state="PENDING",
            participants=json.dumps(participants, ensure_ascii=False),
            artifacts="[]",
            status="running",
            context_json="{}",
            started_at=datetime.utcnow(),
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)
        logger.info("Created instance %s from template '%s' for project %s", instance_id, config.name, payload.project_id)
        return _instance_to_response(instance)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to instantiate template %d", config_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/{config_id}", response_model=Dict[str, bool])
async def delete_workflow_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(WorkflowConfigModel).filter(WorkflowConfigModel.id == config_id).first()
    if config is None:
        raise HTTPException(status_code=404, detail=f"Workflow config {config_id} not found")
    if config.is_template:
        raise HTTPException(status_code=403, detail="Cannot delete preset template")
    try:
        db.delete(config)
        db.commit()
        logger.info("Deleted workflow config '%s' (id=%d)", config.name, config.id)
        return {"success": True}
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to delete workflow config %d", config_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


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
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    try:
        config.yaml_path = yaml_path
        db.commit()
        db.refresh(config)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update yaml_path for config %d", config_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    logger.info("Synced workflow config '%s' to YAML: %s", config.name, yaml_path)
    return {"success": True, "yaml_path": yaml_path}
