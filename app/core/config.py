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
from pydantic import BaseSettings, Field, HttpUrl

# Load environment variables from a local .env file if present.
load_dotenv(override=False)


class Settings(BaseSettings):
    app_name: str = Field("Buffalo Winter Elder Help Routing", env="APP_NAME")
    app_base_url: HttpUrl = Field(..., env="APP_BASE_URL")
    google_client_id: str = Field(..., env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    google_auth_scopes: str = Field(
        "openid email profile",
        description="Space-separated scopes requested from Google OAuth.",
        env="GOOGLE_OAUTH_SCOPES",
    )
    database_url: str = Field(
        default=f"sqlite:///{Path.cwd() / 'app.db'}",
        env="DATABASE_URL",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def google_scope_list(self) -> list[str]:
        return [scope for scope in self.google_auth_scopes.split(" ") if scope]

    @property
    def google_redirect_uri(self) -> str:
        return f"{self.app_base_url.rstrip('/')}/auth/google/callback"


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance so the environment is parsed only once.
    """

    return Settings()


settings = get_settings()

