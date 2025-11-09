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
    app_base_url: HttpUrl = Field("http://localhost:8000", env="APP_BASE_URL")
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
    otp_expire_minutes: int = Field(
        5,
        env="OTP_EXPIRE_MINUTES",
        description="Validity window for email one-time passcodes.",
    )
    max_open_requests_per_elder: int = Field(
        default_factory=lambda: 999_999,
        ge=1,
        env="MAX_OPEN_REQUESTS_PER_ELDER",
        description="Maximum number of concurrently open/assigned requests per elder.",
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
    admin_emails_csv: str = Field(
        "",
        env="ADMIN_EMAILS",
        description="Comma separated list of admin email addresses.",
    )
    admin_secret: Optional[str] = Field(
        None,
        env="ADMIN_SECRET",
        description="Optional shared secret allowing admin endpoints.",
    )
    database_url: str = Field(
        default="sqlite:///./app.db",
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

    @property
    def admin_email_allowlist(self) -> set[str]:
        return {
            email.strip().lower()
            for email in self.admin_emails_csv.split(",")
            if email.strip()
        }

@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance so the environment is parsed only once.
    """

    return Settings()


settings = get_settings()

