"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Scientist-Bin backend.

    All fields use the ``SCIENTIST_BIN_`` env-var prefix except
    ``google_api_key`` which reads from the standard ``GOOGLE_API_KEY``.
    """

    model_config = SettingsConfigDict(
        env_prefix="SCIENTIST_BIN_",
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )

    google_api_key: str = Field(
        ...,
        validation_alias=AliasChoices("GOOGLE_API_KEY", "SCIENTIST_BIN_GOOGLE_API_KEY"),
    )
    gemini_model: str = "gemini-2.0-flash"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()  # type: ignore[call-arg]
