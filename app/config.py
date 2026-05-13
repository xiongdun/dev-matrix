from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "sqlite:///./devmatrix.db"
    redis_url: str = "redis://localhost:6379/0"
    temporal_host: str = "localhost:7233"

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    default_llm_provider: str = "openai"
    default_llm_model: str = "gpt-4"
    llm_strategy: str = "quality_first"

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    default_locale: str = "zh"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
