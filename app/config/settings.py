"""
Application configuration contract.

This module defines ONLY the settings schema for the application, loaded
from environment variables / a .env file via pydantic-settings. It
contains no business logic, no AI logic, and makes no API calls.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration.

    Values are read from environment variables and/or a `.env` file in the
    project root. Add provider-specific configuration (e.g. LLM API keys,
    base URLs) in future sprints as needed.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI BrandPilot"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_embedding_model: str = "nomic-embed-text"

    # Email notifications: sent when a draft is ready for human approval
    # (Sprint 13 -- see app/services/notification_service.py). Nothing is
    # ever auto-published; email is purely "please review this" outreach.
    # Leave smtp_host empty to disable notifications entirely.
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    notify_to_email: Optional[str] = None


settings = Settings()
