from functools import lru_cache
from pathlib import Path
from decimal import Decimal
from typing import Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "rub-rate-bot"
    log_level: str = "INFO"
    start_polling: bool = False

    database_url: str = "sqlite+aiosqlite:///./rub_rate_bot.db"

    telegram_bot_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "BOT_TOKEN"),
    )
    telegram_api_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("TELEGRAM_API_ID", "API_ID"),
    )
    telegram_api_hash: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TELEGRAM_API_HASH", "API_HASH"),
    )
    telethon_session_name: str = "rub_rate_bot"
    nobitex_source: str | None = None
    rapira_source: str | None = None
    rate_margin_percent: Decimal = Field(
        default=Decimal("3.56"),
        validation_alias=AliasChoices("MARGIN_PERCENT", "RATE_MARGIN_PERCENT"),
    )
    auto_notify_admins_on_parse_error: bool = False
    rate_refresh_mode: str = "aligned_5min"
    rate_refresh_every_minutes: int = 5
    rate_refresh_delay_seconds: int = 15
    fetch_last_messages_limit: int = 10

    admin_ids: list[int] = Field(default_factory=list)
    admin_usernames: list[str] = Field(default_factory=list)

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: Any) -> list[int] | Any:
        if isinstance(value, str) and not value.strip().startswith("["):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return value

    @field_validator("admin_usernames", mode="before")
    @classmethod
    def parse_admin_usernames(cls, value: Any) -> list[str] | Any:
        if isinstance(value, str) and not value.strip().startswith("["):
            return [item.strip().removeprefix("@") for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
