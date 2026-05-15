"""数据库模型模块。

定义 SQLAlchemy ORM 模型和数据库连接管理。
包含 ProjectStateModel 和 StateSnapshotModel 两个核心模型，
以及数据库引擎和会话管理函数。

主要类/函数：
    - ProjectStateModel: 项目状态模型。
    - StateSnapshotModel: 状态快照模型。
    - get_engine: 获取数据库引擎。
    - get_session_maker: 获取会话工厂。
    - init_db: 初始化数据库表。
    - get_db: 生成数据库会话的依赖函数。

使用示例：
    ```python
    from app.state.models import init_db, get_db

    init_db()
    db = next(get_db())
    ```
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

Base = declarative_base()


class ProjectStateModel(Base):
    """项目状态模型。

    存储项目的当前状态 JSON 和状态标识。

    Attributes:
        id: 主键 ID。
        project_id: 项目唯一标识。
        state_json: 状态 JSON 字符串。
        status: 状态标识字符串。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "project_states"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), unique=True, index=True, nullable=False)
    state_json = Column(Text, default="{}")
    status = Column(String(32), default="pending")
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StateSnapshotModel(Base):
    """状态快照模型。

    存储项目状态的历史快照，用于回滚。

    Attributes:
        id: 主键 ID。
        project_id: 项目标识。
        state_json: 快照时的状态 JSON。
        status: 快照时的状态标识。
        created_at: 快照创建时间。
    """

    __tablename__ = "state_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    state_json = Column(Text, default="{}")
    status = Column(String(32), default="pending")
    stage_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowConfigModel(Base):
    """工作流配置/模板模型。

    存储 Vue Flow 可视化编辑器设计的工作流配置。
    当 is_template=True 时，该记录为预置流程模板，不可删除。

    Attributes:
        id: 主键 ID。
        name: 工作流配置名称。
        description: 工作流配置描述。
        version: 版本号。
        flow_json: Vue Flow 的 nodes/edges JSON。
        yaml_path: 同步保存的 YAML 文件路径。
        status: 配置状态 (draft/active/archived)。
        is_template: 是否为预置模板。
        category: 模板分类 (standard/hotfix/db_change/auto_fix)。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "workflow_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text, default="")
    version = Column(String(16), default="1.0.0")
    flow_json = Column(Text, default="{}")
    yaml_path = Column(String(256), nullable=True)
    status = Column(String(32), default="draft")
    is_template = Column(Integer, default=0)
    category = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkflowInstanceModel(Base):
    """工作流实例模型。

    一个需求对应一个流程实例，记录实例的运行时状态。

    Attributes:
        id: 主键 ID。
        instance_id: 业务编号（如 WF-2026-001）。
        template_id: 引用的模板 ID（关联 WorkflowConfigModel）。
        project_id: 关联的需求项目 ID。
        current_state: 当前阶段状态（如 ARCHITECTURE_REVIEW）。
        participants: 参与的 Agent 角色列表 JSON。
        artifacts: 产出物列表 JSON（如 [{"name": "prd_v2.md", "stage": "generate_prd"}]）。
        status: 实例状态 (running/paused/completed/failed/cancelled)。
        context_json: 运行时上下文 JSON。
        started_at: 实例启动时间。
        completed_at: 实例完成时间。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "workflow_instances"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(String(32), unique=True, index=True, nullable=False)
    template_id = Column(Integer, nullable=True)
    project_id = Column(String(64), index=True, nullable=False)
    current_state = Column(String(64), default="PENDING")
    participants = Column(Text, default="[]")
    artifacts = Column(Text, default="[]")
    status = Column(String(32), default="running")
    context_json = Column(Text, default="{}")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkflowTaskModel(Base):
    """工作台任务模型。

    存储工作流中各阶段的待办任务，供 Workbench 界面展示和操作。

    Attributes:
        id: 主键 ID。
        project_id: 项目唯一标识。
        workflow_id: 关联的工作流配置 ID。
        stage_id: 工作流阶段 ID（如 analyze_requirement）。
        stage_name: 阶段显示名称（如 Requirement Analysis）。
        agent_role: 对应的 Agent 角色（如 business_analyst）。
        status: 任务状态 (pending/approved/rejected/retrying/completed)。
        output_json: AI 产出物 JSON。
        feedback: 用户反馈意见。
        arrived_at: 任务到达时间。
        processed_at: 处理时间。
        created_at: 创建时间。
        updated_at: 更新时间。
    """

    __tablename__ = "workflow_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(64), index=True, nullable=False)
    workflow_id = Column(Integer, nullable=True)
    stage_id = Column(String(64), nullable=False)
    stage_name = Column(String(128), nullable=False)
    agent_role = Column(String(64), index=True, nullable=False)
    status = Column(String(32), default="pending")
    output_json = Column(Text, default="{}")
    feedback = Column(Text, nullable=True)
    arrived_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


@event.listens_for(ProjectStateModel, "before_update")
def receive_before_update(mapper, connection, target):
    """在更新 ProjectStateModel 前自动设置 updated_at 时间戳。"""
    target.updated_at = datetime.utcnow()


@event.listens_for(WorkflowConfigModel, "before_update")
def workflow_config_before_update(mapper, connection, target):
    """在更新 WorkflowConfigModel 前自动设置 updated_at 时间戳。"""
    target.updated_at = datetime.utcnow()


@event.listens_for(WorkflowInstanceModel, "before_update")
def workflow_instance_before_update(mapper, connection, target):
    """在更新 WorkflowInstanceModel 前自动设置 updated_at 时间戳。"""
    target.updated_at = datetime.utcnow()


@event.listens_for(WorkflowTaskModel, "before_update")
def workflow_task_before_update(mapper, connection, target):
    """在更新 WorkflowTaskModel 前自动设置 updated_at 时间戳。"""
    target.updated_at = datetime.utcnow()


# 模块级单例
_engine = None
_SessionLocal = None


def get_engine():
    """获取数据库引擎（单例）。

    首次调用时根据配置创建引擎，SQLite 使用 check_same_thread=False。

    Returns:
        Engine: SQLAlchemy 引擎实例。
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False}
            if settings.database_url.startswith("sqlite")
            else {},
        )
    return _engine


def get_session_maker():
    """获取会话工厂（单例）。

    Returns:
        sessionmaker: SQLAlchemy 会话工厂。
    """
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def init_db():
    """初始化数据库，创建所有表。"""
    Base.metadata.create_all(bind=get_engine())


def get_db():
    """生成数据库会话的生成器，用于 FastAPI 依赖注入。

    Yields:
        Session: 数据库会话。
    """
    Session = get_session_maker()
    db = Session()
    try:
        yield db
    finally:
        db.close()
