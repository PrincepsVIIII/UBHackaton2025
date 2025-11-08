# -*- coding: utf-8 -*-
"""
Application configuration utilities.

Loads environment variables and exposes a singleton settings object that other
modules can import.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import EmailStr, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from a local .env file if present.
load_dotenv(override=False)


class Settings(BaseSettings):
    app_name: str = Field("Buffalo Winter Elder Help Routing", env="APP_NAME")
    app_base_url: HttpUrl = Field(..., env="APP_BASE_URL")
    secret_key: str = Field(
        "change-this-secret-key",
        env="SECRET_KEY",
        description="Secret used for signing JWT tokens. Override in production.",
    )
    access_token_expire_minutes: int = Field(
        60 * 24,
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="Expiry window for session tokens issued after login.",
    )
    login_token_expire_minutes: int = Field(
        15,
        env="LOGIN_TOKEN_EXPIRE_MINUTES",
        description="Expiry window for passwordless magic links.",
    )
    email_from: EmailStr = Field(
        "noreply@example.com",
        env="EMAIL_FROM",
        description="From address used when sending login emails.",
    )
    smtp_host: Optional[str] = Field(None, env="SMTP_HOST")
    smtp_port: Optional[int] = Field(None, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(None, env="SMTP_PASSWORD")
    use_console_email: bool = Field(
        True,
        env="EMAIL_USE_CONSOLE",
        description="When true, login links are printed to console instead of emailing.",
    )
    database_url: str = Field(
        default=f"sqlite:///{Path.cwd() / 'app.db'}",
        env="DATABASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Legacy / optional environment variables for compatibility.
    port: Optional[int] = Field(default=8000, env="PORT")
    jwt_secret: Optional[str] = Field(default=None, env="JWT_SECRET")
    google_maps_api_key: Optional[str] = Field(default=None, env="GOOGLE_MAPS_API_KEY")

@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance so the environment is parsed only once.
    """

    return Settings()


settings = get_settings()

