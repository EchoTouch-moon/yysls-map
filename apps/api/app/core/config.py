from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://localhost/yysls_map"
    web_origin: str = "http://localhost:3000"
    admin_username: str = "admin"
    admin_password_hash: str = ""
    session_secret: str = Field(
        default="development-only-session-secret-change-me",
        min_length=32,
    )
    session_ttl_minutes: int = Field(default=30, ge=5, le=240)
    rate_limit_backend: Literal["memory", "database"] = "database"
    llm_enabled: bool = False
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "mimo-v2.5-pro"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
