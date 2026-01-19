"""应用配置（基于 pydantic-settings）。

约定：
- 默认读取项目根目录下的 .env（如存在）
- 支持环境变量覆盖
"""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}


class Settings(BaseSettings):
    """应用配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    database_url: str = Field(
        default="sqlite+aiosqlite:///./interview_data.db",
        validation_alias="DATABASE_URL",
        description="数据库连接字符串",
    )

    log_level: str = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
        description="日志级别（DEBUG/INFO/WARNING/ERROR）",
    )

    allowed_origins: list[str] = Field(
        default_factory=list,
        validation_alias="ALLOWED_ORIGINS",
        description="CORS 允许的来源列表（逗号分隔）",
    )

    admin_token: str = Field(
        default="",
        validation_alias="ADMIN_TOKEN",
        description="后台监管接口 Token（使用 X-Admin-Token 访问）。为空则禁用后台监管接口。",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_allowed_origins(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        raise TypeError("ALLOWED_ORIGINS 必须为逗号分隔字符串或字符串列表")

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: Any) -> str:
        if value is None:
            return "INFO"
        return str(value).upper().strip()

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        if value not in _LOG_LEVELS:
            raise ValueError(f"log_level 必须为 {_LOG_LEVELS} 之一")
        return value
