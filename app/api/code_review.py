"""代码审查 API 模块。"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.code_reviewer import CodeReviewerAgent
from app.api.deps import get_db
from app.state.models import CodeReviewModel, WorkflowTaskModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["code-reviews"])


class CreateCodeReviewRequest(BaseModel):
    """创建代码审查请求。"""

    task_id: int = Field(..., description="关联的工作流任务 ID")
    diff: str = Field(..., description="代码 diff 内容")
    project_context: str = Field(default="", description="项目上下文信息")
    model: str | None = Field(default=None, description="指定 LLM 模型")


class CodeReviewIssue(BaseModel):
    """代码审查问题项。"""

    file: str
    line: int | None = None
    severity: str
    category: str
    title: str
    description: str
    suggestion: str


class CodeReviewResponse(BaseModel):
    """代码审查响应。"""

    id: int
    task_id: int
    project_id: str
    status: str
    score: int | None = None
    summary: str | None = None
    issues: list[CodeReviewIssue] = []
    improvements: list[dict[str, str]] = []
    llm_model: str | None = None
    duration_ms: int | None = None
    created_at: str
    completed_at: str | None = None

    class Config:
        from_attributes = True


@router.post("", response_model=CodeReviewResponse)
async def create_code_review(
    payload: CreateCodeReviewRequest,
    db: Session = Depends(get_db),
) -> CodeReviewModel:
    """创建代码审查。"""
    # 验证任务存在
    task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {payload.task_id} not found")

    # 创建审查记录
    review = CodeReviewModel(
        task_id=payload.task_id,
        project_id=task.project_id,
        status="running",
        raw_diff=payload.diff,
        llm_model=payload.model,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    # 异步执行审查
    try:
        agent = CodeReviewerAgent()
        report = await agent.execute(
            {
                "diff": payload.diff,
                "project_context": payload.project_context,
                "model": payload.model,
            }
        )

        # 更新审查记录
        review.status = "completed"
        review.score = report.get("score")
        review.summary = report.get("summary")
        review.issues_json = json.dumps(report.get("issues", []))
        review.improvements_json = json.dumps(report.get("improvements", []))
        review.duration_ms = report.get("duration_ms")
        review.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(review)

    except Exception as e:
        logger.exception("Code review failed for task %d", payload.task_id)
        review.status = "failed"
        review.summary = f"审查失败：{e}"
        db.commit()
        db.refresh(review)

    return review


@router.get("/{review_id}", response_model=CodeReviewResponse)
async def get_code_review(
    review_id: int,
    db: Session = Depends(get_db),
) -> CodeReviewModel:
    """获取代码审查详情。"""
    review = db.query(CodeReviewModel).filter(CodeReviewModel.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail=f"Code review {review_id} not found")
    return review


@router.get("", response_model=list[CodeReviewResponse])
async def list_code_reviews(
    task_id: int | None = None,
    project_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[CodeReviewModel]:
    """列出代码审查记录。"""
    query = db.query(CodeReviewModel)

    if task_id:
        query = query.filter(CodeReviewModel.task_id == task_id)
    if project_id:
        query = query.filter(CodeReviewModel.project_id == project_id)
    if status:
        query = query.filter(CodeReviewModel.status == status)

    reviews = query.order_by(CodeReviewModel.created_at.desc()).offset(offset).limit(limit).all()
    return reviews


@router.post("/{review_id}/re-run")
async def rerun_code_review(
    review_id: int,
    db: Session = Depends(get_db),
) -> CodeReviewResponse:
    """重新运行代码审查。"""
    review = db.query(CodeReviewModel).filter(CodeReviewModel.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail=f"Code review {review_id} not found")

    if not review.raw_diff:
        raise HTTPException(status_code=400, detail="No diff content to review")

    # 重置状态
    review.status = "running"
    review.score = None
    review.summary = None
    review.issues_json = None
    review.improvements_json = None
    review.completed_at = None
    db.commit()

    # 重新执行审查
    try:
        agent = CodeReviewerAgent()
        report = await agent.execute(
            {
                "diff": review.raw_diff,
                "model": review.llm_model,
            }
        )

        review.status = "completed"
        review.score = report.get("score")
        review.summary = report.get("summary")
        review.issues_json = json.dumps(report.get("issues", []))
        review.improvements_json = json.dumps(report.get("improvements", []))
        review.duration_ms = report.get("duration_ms")
        review.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(review)

    except Exception as e:
        logger.exception("Code review re-run failed for review %d", review_id)
        review.status = "failed"
        review.summary = f"审查失败：{e}"
        db.commit()
        db.refresh(review)

    return review
