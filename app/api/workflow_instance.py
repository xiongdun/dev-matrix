"""工作流实例 API 模块。

提供工作流实例的查询、状态更新和产出物管理接口。

主要端点：
    - GET /workflow-instances/ - 列出所有实例
    - GET /workflow-instances/{instance_id} - 获取实例详情
    - GET /workflow-instances/by-project/{project_id} - 按项目查询实例
    - POST /workflow-instances/{instance_id}/artifacts - 添加产出物
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.state.models import WorkflowInstanceModel, get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class ArtifactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    stage: str = Field(..., min_length=1, max_length=64)
    content: Optional[str] = None


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


@router.get("/", response_model=Dict[str, List[WorkflowInstanceResponse]])
async def list_instances(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        query = db.query(WorkflowInstanceModel)
        if status:
            query = query.filter(WorkflowInstanceModel.status == status)
        instances = query.order_by(WorkflowInstanceModel.id.desc()).all()
        logger.info("Listed %d workflow instances (status=%s)", len(instances), status)
        return {"instances": [_instance_to_response(i) for i in instances]}
    except Exception as exc:
        logger.exception("Failed to list workflow instances")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/by-project/{project_id}", response_model=WorkflowInstanceResponse)
async def get_instance_by_project(project_id: str, db: Session = Depends(get_db)):
    instance = db.query(WorkflowInstanceModel).filter(
        WorkflowInstanceModel.project_id == project_id,
    ).order_by(WorkflowInstanceModel.id.desc()).first()
    if instance is None:
        raise HTTPException(status_code=404, detail=f"No instance found for project '{project_id}'")
    return _instance_to_response(instance)


@router.get("/{instance_id_str}", response_model=WorkflowInstanceResponse)
async def get_instance(instance_id_str: str, db: Session = Depends(get_db)):
    instance = db.query(WorkflowInstanceModel).filter(
        WorkflowInstanceModel.instance_id == instance_id_str
    ).first()
    if instance is None:
        raise HTTPException(status_code=404, detail=f"Instance '{instance_id_str}' not found")
    return _instance_to_response(instance)


@router.post("/{instance_id_str}/artifacts", response_model=WorkflowInstanceResponse)
async def add_artifact(instance_id_str: str, payload: ArtifactCreate, db: Session = Depends(get_db)):
    instance = db.query(WorkflowInstanceModel).filter(
        WorkflowInstanceModel.instance_id == instance_id_str
    ).first()
    if instance is None:
        raise HTTPException(status_code=404, detail=f"Instance '{instance_id_str}' not found")
    try:
        artifacts = json.loads(instance.artifacts) if instance.artifacts else []
        artifacts.append({"name": payload.name, "stage": payload.stage, "content": payload.content})
        instance.artifacts = json.dumps(artifacts, ensure_ascii=False)
        db.commit()
        db.refresh(instance)
        logger.info("Added artifact '%s' to instance %s", payload.name, instance_id_str)
        return _instance_to_response(instance)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to add artifact to instance %s", instance_id_str)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
