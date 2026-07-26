"""
Application configuration contract.

This module defines ONLY the settings schema for the application, loaded
from environment variables / a .env file via pydantic-settings. It
contains no business logic, no AI logic, and makes no API calls.
"""

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


settings = Settings()
