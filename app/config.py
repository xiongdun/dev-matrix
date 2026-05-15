"""DevMatrix 应用程序配置模块。

该模块定义了应用程序的设置模型，并提供了一个缓存的设置获取函数。
支持从环境变量和 .env 文件加载配置。

主要类/函数：
    - Settings: Pydantic 设置模型，定义所有配置项。
    - get_settings: 返回缓存的 Settings 实例。

使用示例：
    ```python
    from app.config import get_settings

    settings = get_settings()
    db_url = settings.database_url
    ```

Attributes:
    None
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用程序配置模型。

    所有配置项均可通过环境变量覆盖，支持从 .env 文件加载。

    Attributes:
        database_url: 数据库连接 URL，默认 SQLite。
        redis_url: Redis 连接 URL。
        temporal_host: Temporal 工作流引擎主机地址。
        openai_api_key: OpenAI API 密钥。
        anthropic_api_key: Anthropic API 密钥。
        default_llm_provider: 默认 LLM 提供商。
        default_llm_model: 默认 LLM 模型。
        llm_strategy: LLM 选择策略。
        app_host: 应用监听主机。
        app_port: 应用监听端口。
        debug: 是否启用调试模式。
        default_locale: 默认语言区域设置。
    """

    # 数据库配置
    database_url: str = "sqlite:///./devmatrix.db"
    redis_url: str = "redis://localhost:6379/0"
    temporal_host: str = "localhost:7233"

    # LLM API 密钥
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # LLM 配置
    default_llm_provider: str = "openai"
    default_llm_model: str = "gpt-4"
    llm_strategy: str = "quality_first"

    # 应用服务器配置
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # 国际化配置
    default_locale: str = "zh"

    class Config:
        """Pydantic 配置类。"""
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的 Settings 实例。

    使用 lru_cache 确保整个应用生命周期中只创建一个 Settings 实例。

    Returns:
        Settings: 应用程序配置实例。

    Example:
        ```python
        settings = get_settings()
        print(settings.database_url)
        ```
    """
    return Settings()
