"""系统设置 API 模块。

提供系统配置的增删改查接口，支持分类管理和敏感字段脱敏。
配置值持久化到数据库，应用启动时从环境变量初始化默认值。

主要端点：
    - GET /settings - 获取所有配置（敏感字段脱敏）
    - GET /settings/categories - 获取配置分类列表
    - GET /settings/{key} - 获取单个配置
    - PUT /settings - 批量更新配置
    - POST /settings/init - 从环境变量初始化默认配置

使用示例：
    ```python
    from app.api.settings import router
    app.include_router(router, prefix="/settings", tags=["settings"])
    ```
"""

import logging
import os
from typing import Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.state.models import SystemConfigModel, get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# 默认配置定义：key -> (默认值, 分类, 描述, 是否敏感)
DEFAULT_CONFIGS: Dict[str, tuple] = {
    # 系统设置
    "app_name": ("DevMatrix", "system", "应用名称", False),
    "theme": ("auto", "system", "主题设置 (light/dark/auto)", False),
    "language": ("zh", "system", "默认语言 (zh/en)", False),
    "notifications_enabled": ("true", "system", "是否启用通知", False),
    "auto_save_interval": ("30000", "system", "自动保存间隔 (毫秒)", False),

    # LLM 设置
    "llm_provider": ("openai", "llm", "默认 LLM 提供商", False),
    "llm_model": ("gpt-4", "llm", "默认 LLM 模型", False),
    "llm_strategy": ("quality_first", "llm", "LLM 选择策略", False),
    "openai_api_key": ("", "llm", "OpenAI API 密钥", True),
    "anthropic_api_key": ("", "llm", "Anthropic API 密钥", True),
    "openai_base_url": ("https://api.openai.com/v1", "llm", "OpenAI API 基础地址", False),
    "anthropic_base_url": ("https://api.anthropic.com/v1", "llm", "Anthropic API 基础地址", False),

    # 数据库设置
    "database_url": ("sqlite:///./devmatrix.db", "database", "数据库连接 URL", True),
    "redis_url": ("redis://localhost:6379/0", "database", "Redis 连接 URL", True),
    "temporal_host": ("localhost:7233", "database", "Temporal 主机地址", False),

    # 安全设置
    "session_timeout": ("3600", "security", "会话超时时间 (秒)", False),
    "max_login_attempts": ("5", "security", "最大登录尝试次数", False),
}


class ConfigItemResponse(BaseModel):
    """配置项响应模型。"""

    key: str
    value: str
    category: str
    description: Optional[str] = None
    is_sensitive: bool = False
    updated_at: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型。"""

    configs: Dict[str, str] = Field(..., description="要更新的配置键值对")


class ConfigListResponse(BaseModel):
    """配置列表响应模型。"""

    configs: List[ConfigItemResponse]


class CategoriesResponse(BaseModel):
    """分类列表响应模型。"""

    categories: List[str]


def _mask_sensitive(value: str) -> str:
    """对敏感值进行脱敏处理。

    保留前4位和后4位，中间用 * 代替。

    Args:
        value: 原始值。

    Returns:
        str: 脱敏后的值。
    """
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


def _model_to_response(model: SystemConfigModel, mask: bool = True) -> ConfigItemResponse:
    """将数据库模型转换为响应模型。

    Args:
        model: SystemConfigModel 实例。
        mask: 是否对敏感字段脱敏。

    Returns:
        ConfigItemResponse: 响应模型。
    """
    value = cast(str, model.value)
    is_sensitive = bool(cast(int, model.is_sensitive))

    if mask and is_sensitive and value:
        value = _mask_sensitive(value)

    return ConfigItemResponse(
        key=cast(str, model.key),
        value=value,
        category=cast(str, model.category),
        description=cast(Optional[str], model.description),
        is_sensitive=is_sensitive,
        updated_at=cast(Optional[str], model.updated_at.isoformat() if model.updated_at else None),
    )


def init_default_configs(db: Session) -> None:
    """从环境变量初始化默认配置。

    如果数据库中不存在某配置，则使用默认值（优先从环境变量读取）。

    Args:
        db: 数据库会话。
    """
    # 环境变量映射：配置键 -> 环境变量名
    env_mapping = {
        "openai_api_key": "OPENAI_API_KEY",
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "database_url": "DATABASE_URL",
        "redis_url": "REDIS_URL",
        "temporal_host": "TEMPORAL_HOST",
        "llm_provider": "DEFAULT_LLM_PROVIDER",
        "llm_model": "DEFAULT_LLM_MODEL",
        "llm_strategy": "LLM_STRATEGY",
    }

    for key, (default_value, category, description, is_sensitive) in DEFAULT_CONFIGS.items():
        existing = db.query(SystemConfigModel).filter(SystemConfigModel.key == key).first()
        if existing is None:
            # 优先从环境变量读取
            env_var = env_mapping.get(key)
            value = os.environ.get(env_var, default_value) if env_var else default_value

            config = SystemConfigModel(
                key=key,
                value=value,
                category=category,
                description=description,
                is_sensitive=1 if is_sensitive else 0,
            )
            db.add(config)
            logger.info("Initialized config: %s = %s", key, "***" if is_sensitive else value)

    db.commit()


@router.get("", response_model=ConfigListResponse)
async def list_configs(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取所有配置列表。

    敏感字段会自动脱敏处理。

    Args:
        category: 按分类筛选（可选）。
        db: 数据库会话。

    Returns:
        ConfigListResponse: 配置列表。
    """
    query = db.query(SystemConfigModel)
    if category:
        query = query.filter(SystemConfigModel.category == category)

    configs = query.order_by(SystemConfigModel.category, SystemConfigModel.key).all()
    return ConfigListResponse(configs=[_model_to_response(c) for c in configs])


@router.get("/categories", response_model=CategoriesResponse)
async def list_categories(db: Session = Depends(get_db)):
    """获取所有配置分类列表。

    Args:
        db: 数据库会话。

    Returns:
        CategoriesResponse: 分类列表。
    """
    categories = (
        db.query(SystemConfigModel.category)
        .distinct()
        .order_by(SystemConfigModel.category)
        .all()
    )
    return CategoriesResponse(categories=[c[0] for c in categories])


@router.post("/init")
async def initialize_configs(db: Session = Depends(get_db)):
    """手动触发配置初始化。

    从环境变量和默认值初始化缺失的配置项。

    Args:
        db: 数据库会话。

    Returns:
        dict: 初始化结果。
    """
    init_default_configs(db)
    return {"status": "ok", "message": "Configs initialized from environment"}


@router.get("/{key}", response_model=ConfigItemResponse)
async def get_config(key: str, db: Session = Depends(get_db)):
    """获取单个配置项。

    Args:
        key: 配置键。
        db: 数据库会话。

    Returns:
        ConfigItemResponse: 配置项。

    Raises:
        HTTPException: 配置不存在时返回 404。
    """
    config = db.query(SystemConfigModel).filter(SystemConfigModel.key == key).first()
    if config is None:
        raise HTTPException(status_code=404, detail=f"Config '{key}' not found")
    return _model_to_response(config)


@router.put("", response_model=ConfigListResponse)
async def update_configs(
    payload: ConfigUpdateRequest,
    db: Session = Depends(get_db),
):
    """批量更新配置。

    Args:
        payload: 包含要更新的键值对。
        db: 数据库会话。

    Returns:
        ConfigListResponse: 更新后的配置列表。

    Raises:
        HTTPException: 更新失败时返回 500。
    """
    updated_keys = []

    try:
        for key, value in payload.configs.items():
            config = db.query(SystemConfigModel).filter(SystemConfigModel.key == key).first()
            if config is None:
                # 如果配置不存在，尝试从 DEFAULT_CONFIGS 获取元数据创建
                meta = DEFAULT_CONFIGS.get(key)
                if meta:
                    default_value, category, description, is_sensitive = meta
                    config = SystemConfigModel(
                        key=key,
                        value=value,
                        category=category,
                        description=description,
                        is_sensitive=1 if is_sensitive else 0,
                    )
                    db.add(config)
                else:
                    # 未知配置，创建为通用类型
                    config = SystemConfigModel(
                        key=key,
                        value=value,
                        category="custom",
                        description=None,
                        is_sensitive=0,
                    )
                    db.add(config)
            else:
                config.value = value  # type: ignore[assignment]

            updated_keys.append(key)

        db.commit()
        logger.info("Updated configs: %s", updated_keys)

        # 返回更新后的配置
        configs = (
            db.query(SystemConfigModel)
            .filter(SystemConfigModel.key.in_(updated_keys))
            .all()
        )
        return ConfigListResponse(configs=[_model_to_response(c) for c in configs])

    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update configs")
        raise HTTPException(status_code=500, detail=f"Update failed: {exc}") from exc
