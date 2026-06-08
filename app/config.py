"""DevMatrix 应用程序配置模块。"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用程序配置模型，支持从环境变量和 .env 文件加载。"""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # 数据库配置
    database_url: str = "sqlite:///./devmatrix.db"
    redis_url: str = "redis://localhost:***@localhost:6379/0"
    temporal_host: str = "localhost:7233"

    # LLM API
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_base_url: str = "https://api.anthropic.com/v1"

    # LLM 路由
    default_llm_provider: str = "anthropic"
    default_llm_model: str = "mimo-v2.5-pro"
    llm_strategy: str = "quality_first"

    # Claude Code SDK
    sdk_max_turns: int = 20
    sdk_sandbox_enabled: bool = True

    # OpenAI Agents SDK
    openai_agents_model: str = "mimo-v2.5-pro"
    openai_agents_api_key: str = ""
    openai_agents_base_url: str = ""

    # 应用
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    default_locale: str = "zh"


@lru_cache
def get_settings() -> Settings:
    """获取缓存的 Settings 实例。"""
    return Settings()
