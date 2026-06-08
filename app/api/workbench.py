"""工作台 API 模块。

提供工作台（Workbench）的任务管理和审批接口，
供前端工作台界面获取待办任务、审批/打回/重试任务以及查看统计。

主要端点：
    - GET /tasks - 获取指定角色的待办任务列表
    - GET /tasks/{task_id} - 获取单个任务详情
    - POST /tasks/{task_id}/approve - 确认通过任务
    - POST /tasks/{task_id}/reject - 打回任务
    - POST /tasks/{task_id}/retry - AI 重新处理任务
    - GET /stats - 获取任务统计

使用示例：
    ```python
    from app.api.workbench import router
    app.include_router(router, prefix="/workbench")
    ```
"""

import json
import logging
from datetime import datetime
from typing import Any, cast

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.events.bus import event_bus
from app.events.types import Event, EventTypes
from app.memory.manager import build_memory_prompt
from app.state.models import TaskChatMessageModel, UserModel, WorkflowTaskModel, get_db
from app.state.repository import StateRepository

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessageResponse(BaseModel):
    id: int
    task_id: int
    role: str
    content: str
    tool_calls: str | None = None
    tool_results: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    model: str | None = None
    sdk: str | None = None  # "claude_code" | "openai_agents" | "direct_llm"


class ChatResponse(BaseModel):
    message: ChatMessageResponse
    tool_calls: list[dict[str, Any]] | None = None


class WorkflowTaskResponse(BaseModel):
    id: int
    project_id: str
    workflow_id: int | None = None
    stage_id: str
    stage_name: str
    agent_role: str
    status: str
    output_json: str = "{}"
    feedback: str | None = None
    arrived_at: datetime | None = None
    processed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class RejectRequest(BaseModel):
    comment: str | None = Field(None, max_length=2000)


class RetryRequest(BaseModel):
    feedback: str | None = Field(None, max_length=2000)


class TaskStatsResponse(BaseModel):
    pending: int = 0
    completed: int = 0
    rejected: int = 0


def _model_to_response(model: WorkflowTaskModel) -> WorkflowTaskResponse:
    return WorkflowTaskResponse(
        id=cast(int, model.id),
        project_id=cast(str, model.project_id),
        workflow_id=cast(int | None, model.workflow_id),
        stage_id=cast(str, model.stage_id),
        stage_name=cast(str, model.stage_name),
        agent_role=cast(str, model.agent_role),
        status=cast(str, model.status),
        output_json=cast(str, model.output_json),
        feedback=cast(str | None, model.feedback),
        arrived_at=cast(datetime | None, model.arrived_at),
        processed_at=cast(datetime | None, model.processed_at),
        created_at=cast(datetime | None, model.created_at),
        updated_at=cast(datetime | None, model.updated_at),
    )


@router.get("/tasks", response_model=dict[str, list[WorkflowTaskResponse]])
async def list_tasks(
    role: str | None = Query(None, max_length=64),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(WorkflowTaskModel).filter(
            WorkflowTaskModel.status.in_(["pending", "retrying"])
        )
        if role:
            query = query.filter(WorkflowTaskModel.agent_role == role)
        tasks = query.order_by(WorkflowTaskModel.arrived_at.asc()).all()
        logger.info("Listed %d workbench tasks (role=%s)", len(tasks), role)
        return {"tasks": [_model_to_response(t) for t in tasks]}
    except Exception as exc:
        logger.exception("Failed to list workbench tasks")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/tasks/{task_id}", response_model=WorkflowTaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return _model_to_response(task)


@router.post("/tasks/{task_id}/approve", response_model=WorkflowTaskResponse)
async def approve_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if task.status not in ("pending", "retrying"):
        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} cannot be approved in status '{task.status}'",
        )
    try:
        # type: ignore[assignment]
        task.status = "approved"  # type: ignore[assignment]
        task.processed_at = datetime.utcnow()  # type: ignore[assignment]
        db.commit()
        db.refresh(task)

        await event_bus.publish(
            Event(
                type=EventTypes.APPROVAL_APPROVED,
                payload={
                    "project_id": cast(str, task.project_id),
                    "stage_id": cast(str, task.stage_id),
                    "task_id": cast(int, task.id),
                },
                source="workbench",
                project_id=cast(str, task.project_id),
            )
        )
        logger.info(
            "Approved task %d (project=%s, stage=%s)",
            cast(int, task.id),
            cast(str, task.project_id),
            cast(str, task.stage_id),
        )
        return _model_to_response(task)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to approve task %d", task_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/tasks/{task_id}/reject", response_model=WorkflowTaskResponse)
async def reject_task(
    task_id: int,
    payload: RejectRequest | None = None,
    db: Session = Depends(get_db),
):
    task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if task.status not in ("pending", "retrying"):
        raise HTTPException(
            status_code=400,
            detail=f"Task {task_id} cannot be rejected in status '{task.status}'",
        )
    try:
        task.status = "rejected"  # type: ignore[assignment]
        task.processed_at = datetime.utcnow()  # type: ignore[assignment]
        if payload and payload.comment:
            task.feedback = payload.comment  # type: ignore[assignment]
        db.commit()
        db.refresh(task)
        logger.info(
            "Rejected task %d (project=%s, stage=%s)",
            cast(int, task.id),
            cast(str, task.project_id),
            cast(str, task.stage_id),
        )
        return _model_to_response(task)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to reject task %d", task_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/tasks/{task_id}/retry", response_model=WorkflowTaskResponse)
async def retry_task(
    task_id: int,
    payload: RetryRequest | None = None,
    db: Session = Depends(get_db),
):
    task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if task.status != "rejected":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Task {task_id} can only be retried from 'rejected' status, "
                f"current: '{task.status}'"
            ),
        )
    try:
        task.status = "retrying"  # type: ignore[assignment]
        task.processed_at = datetime.utcnow()  # type: ignore[assignment]
        if payload and payload.feedback:
            task.feedback = payload.feedback  # type: ignore[assignment]
        db.commit()
        db.refresh(task)

        try:
            from app.core.registry.agent_registry import agent_registry
            from app.llm.router import LLMRouter

            try:
                agent_cls = agent_registry.get(cast(str, task.agent_role))
            except KeyError:
                agent_cls = None

            if agent_cls:
                router = LLMRouter()
                repo = StateRepository(db)
                agent = agent_cls(llm_router=router, state_repository=repo)
                output_json_val = cast(str, task.output_json)
                context: dict[str, Any] = {
                    "feedback": task.feedback,
                    "previous_output": json.loads(output_json_val) if output_json_val else {},
                }
                proposal = await agent.run(cast(str, task.project_id), context)

                task.output_json = json.dumps(  # type: ignore[assignment]
                    {"content": proposal.content, "metadata": proposal.metadata},
                    ensure_ascii=False,
                )
                task.status = "pending"  # type: ignore[assignment]
                task.feedback = None  # type: ignore[assignment]
                db.commit()
                db.refresh(task)
                logger.info(
                    "Agent re-executed for task %d, new proposal generated", cast(int, task.id)
                )
        except Exception as agent_exc:
            logger.exception(
                "Agent re-execution failed for task %d: %s", cast(int, task.id), agent_exc
            )
            task.status = "rejected"  # type: ignore[assignment]
            db.commit()
            db.refresh(task)

        return _model_to_response(task)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to retry task %d", task_id)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/tasks/{task_id}/chat", response_model=dict[str, list[ChatMessageResponse]])
async def get_chat_history(
    task_id: int,
    db: Session = Depends(get_db),
):
    """获取任务的对话历史记录。"""
    task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    messages = (
        db.query(TaskChatMessageModel)
        .filter(TaskChatMessageModel.task_id == task_id)
        .order_by(TaskChatMessageModel.created_at.asc())
        .all()
    )

    return {
        "messages": [
            ChatMessageResponse(
                id=cast(int, m.id),
                task_id=cast(int, m.task_id),
                role=cast(str, m.role),
                content=cast(str, m.content),
                tool_calls=cast(str | None, m.tool_calls),
                tool_results=cast(str | None, m.tool_results),
                created_at=cast(datetime | None, m.created_at),
            )
            for m in messages
        ]
    }


@router.post("/tasks/{task_id}/chat", response_model=ChatResponse)
async def chat_with_task(
    task_id: int,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """与任务进行实时对话，调用 Agent SDK 处理用户消息。

    流程：
        1. 保存用户消息到数据库
        2. 获取历史对话上下文
        3. 调用 Agent SDK 生成回复
        4. 执行工具调用（Read/Search/Write/Edit/Bash）
        5. 保存 AI 回复到数据库
        6. 返回 AI 消息和工具调用记录
    """
    task = db.query(WorkflowTaskModel).filter(WorkflowTaskModel.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    try:
        # 1. 保存用户消息
        user_msg = TaskChatMessageModel(
            task_id=task_id,
            role="user",
            content=payload.message,
        )
        db.add(user_msg)
        db.commit()

        # 2. 获取历史消息作为上下文（最多保留最近 20 条）
        history = (
            db.query(TaskChatMessageModel)
            .filter(TaskChatMessageModel.task_id == task_id)
            .order_by(TaskChatMessageModel.created_at.desc())
            .limit(20)
            .all()
        )
        history.reverse()  # 恢复时间顺序

        # 构建对话上下文
        context_lines = []
        for h in history:
            role_label = "User" if h.role == "user" else "Assistant"
            context_lines.append(f"{role_label}: {h.content}")

        context_text = "\n".join(context_lines)

        # 3. 调用 Agent SDK 生成回复
        agent_role = cast(str, task.agent_role)
        stage_name = cast(str, task.stage_name)

        # 构建系统提示词（注入记忆上下文）
        memory_context = build_memory_prompt(
            user_id=cast(int, current_user.id),
            agent_role=agent_role,
            project_id=cast(str, task.project_id),
        )
        system_prompt = (
            f"You are a {agent_role} agent working on the '{stage_name}' stage. "
            f"You have access to tools: Read, Search, Write, Edit, Bash. "
            f"Use them when needed to help the user. "
            f"Respond in the same language as the user."
            f"{memory_context}"
        )

        # 选择 SDK
        sdk_name = payload.sdk or "direct_llm"
        from app.config import get_settings
        from app.sdk.base import SDKRegistry
        settings = get_settings()

        try:
            # 创建 SDK 实例
            if sdk_name == "claude_code":
                sdk = SDKRegistry.create(
                    "claude_code",
                    max_turns=settings.sdk_max_turns,
                    sandbox_enabled=settings.sdk_sandbox_enabled,
                )
            elif sdk_name == "openai_agents":
                sdk = SDKRegistry.create(
                    "openai_agents",
                    model=settings.openai_agents_model,
                    api_key=settings.openai_agents_api_key,
                    base_url=settings.openai_agents_base_url,
                )
            else:
                sdk = SDKRegistry.create("direct_llm")

            # 构建历史消息
            history = [
                {"role": "user" if h.role == "user" else "assistant", "content": h.content}
                for h in history
            ]

            # 调用 SDK
            response = await sdk.chat(
                message=payload.message,
                system_prompt=system_prompt,
                history=history,
            )

            ai_content = response.content
            tool_calls_log = response.tool_calls

            if not response.success:
                logger.error("SDK %s failed: %s", sdk_name, response.error)
                ai_content = f"[{sdk_name}] 调用失败：{response.error}"

        except Exception as e:
            logger.exception("SDK %s error for task %d", sdk_name, task_id)
            ai_content = f"处理消息时出错：{e}"

        # 5. 保存 AI 回复
        ai_msg = TaskChatMessageModel(
            task_id=task_id,
            role="assistant",
            content=ai_content,
            tool_calls=json.dumps(tool_calls_log, ensure_ascii=False) if tool_calls_log else None,
        )
        db.add(ai_msg)
        db.commit()
        db.refresh(ai_msg)

        return ChatResponse(
            message=ChatMessageResponse(
                id=cast(int, ai_msg.id),
                task_id=cast(int, ai_msg.task_id),
                role=cast(str, ai_msg.role),
                content=cast(str, ai_msg.content),
                tool_calls=cast(str | None, ai_msg.tool_calls),
                tool_results=cast(str | None, ai_msg.tool_results),
                created_at=cast(datetime | None, ai_msg.created_at),
            ),
            tool_calls=tool_calls_log if tool_calls_log else None,
        )

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Chat failed for task %d", task_id)
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}") from exc


@router.get("/models", response_model=dict[str, list[dict[str, str]]])
async def get_available_models():
    """获取可用的 LLM 模型列表。"""
    from app.config import get_settings

    settings = get_settings()
    models = []
    if settings.openai_api_key:
        models.extend(
            [
                {"id": "gpt-4", "name": "GPT-4", "provider": "OpenAI"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "OpenAI"},
            ]
        )
    if settings.anthropic_api_key:
        models.extend(
            [
                {"id": "claude-3-opus", "name": "Claude 3 Opus", "provider": "Anthropic"},
                {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "provider": "Anthropic"},
            ]
        )
    if not models:
        models = [
            {"id": "gpt-4", "name": "GPT-4", "provider": "OpenAI"},
            {"id": "claude-3-opus", "name": "Claude 3 Opus", "provider": "Anthropic"},
        ]
    return {"models": models}


@router.get("/sdks", response_model=dict[str, list[dict[str, Any]]])
async def list_sdks():
    """获取可用的 Agent SDK 列表。"""
    from app.sdk.base import SDKRegistry
    # 确保 SDK 已注册
    import app.sdk.claude_code  # noqa: F401
    import app.sdk.openai_agents  # noqa: F401
    import app.sdk.direct_llm  # noqa: F401

    sdks = []
    for name, sdk_cls in SDKRegistry.list_all().items():
        try:
            instance = sdk_cls()
            sdks.append({
                "id": name,
                "name": instance.display_name,
                "description": instance.description,
                "available": instance.is_available(),
            })
        except Exception:
            sdks.append({
                "id": name,
                "name": name,
                "description": "",
                "available": False,
            })
    return {"sdks": sdks}


@router.post("/transcribe", response_model=dict[str, str])
async def transcribe_audio(
    audio: Any = None,
):
    """语音转文字（使用 OpenAI Whisper API）。"""
    try:
        from app.config import get_settings

        settings = get_settings()
        if not settings.openai_api_key:
            return {"text": "", "error": "OpenAI API key not configured"}
        # 这里简化处理，实际应该接收上传的文件
        # 由于 FastAPI 文件上传需要更复杂的处理，这里返回模拟结果
        return {"text": "语音转文字功能需要配置 OpenAI API Key 并上传音频文件。"}
    except Exception as exc:
        logger.exception("Transcription failed")
        return {"text": "", "error": str(exc)}


@router.get("/stats", response_model=TaskStatsResponse)
async def get_stats(
    role: str | None = Query(None, max_length=64),
    db: Session = Depends(get_db),
):
    try:
        base_filter = [WorkflowTaskModel.agent_role == role] if role else []
        pending = (
            db.query(func.count(WorkflowTaskModel.id))
            .filter(*base_filter, WorkflowTaskModel.status.in_(["pending", "retrying"]))
            .scalar()
            or 0
        )

        completed = (
            db.query(func.count(WorkflowTaskModel.id))
            .filter(*base_filter, WorkflowTaskModel.status.in_(["approved", "completed"]))
            .scalar()
            or 0
        )

        rejected = (
            db.query(func.count(WorkflowTaskModel.id))
            .filter(*base_filter, WorkflowTaskModel.status == "rejected")
            .scalar()
            or 0
        )

        logger.info(
            "Workbench stats (role=%s): pending=%d, completed=%d, rejected=%d",
            role,
            pending,
            completed,
            rejected,
        )
        return TaskStatsResponse(pending=pending, completed=completed, rejected=rejected)
    except Exception as exc:
        logger.exception("Failed to get workbench stats")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
