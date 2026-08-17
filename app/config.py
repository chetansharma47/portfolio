"""Application settings, loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Environment -------------------------------------------------------
    environment: Literal["development", "preview", "production"] = "development"
    debug: bool = False
    site_name: str = "Chetan Sharma"
    site_url: str = "http://localhost:8000"

    # --- Database ----------------------------------------------------------
    # Neon connection string. Use the pooled endpoint on serverless.
    database_url: str = "sqlite+aiosqlite:///./portfolio.db"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 0

    # --- Security ----------------------------------------------------------
    secret_key: str = "dev-secret-change-me"
    session_cookie_name: str = "portfolio_session"
    csrf_cookie_name: str = "portfolio_csrf"
    session_ttl_minutes: int = 720
    login_max_attempts: int = 8
    login_lockout_minutes: int = 15

    # --- Admin bootstrap ---------------------------------------------------
    admin_email: str = "chetansharmap7@gmail.com"
    admin_password: str | None = None
    admin_path_prefix: str = "/admin"

    # --- Media storage (Vercel Blob) ---------------------------------------
    blob_read_write_token: str | None = None

    # --- Mail (Resend) -----------------------------------------------------
    resend_api_key: str | None = None
    enquiry_to: str = "chetansharmap7@gmail.com"
    enquiry_from: str = "Portfolio Ad Board <onboarding@resend.dev>"

    # --- AI (agent jobs) ---------------------------------------------------
    anthropic_api_key: str | None = None
    agent_model: str = "claude-sonnet-5"
    cron_secret: str | None = None
    job_batch_size: int = 5

    # --- Caching -----------------------------------------------------------
    public_cache_seconds: int = Field(
        default=60,
        description="s-maxage for public pages; admin responses are never cached.",
    )

    @field_validator("database_url")
    @classmethod
    def normalise_database_url(cls, value: str) -> str:
        """Accept the sync URLs that hosting providers hand out.

        `vercel env pull` writes quoted values, so strip those first.
        """
        value = value.strip().strip('"').strip("'")
        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql://", 1)
        if value.startswith("postgresql://"):
            value = value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("sqlite:///"):
            value = value.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return value

    @property
    def is_serverless(self) -> bool:
        return self.environment in {"preview", "production"}

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")

    @property
    def cookie_secure(self) -> bool:
        return self.site_url.startswith("https://")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
