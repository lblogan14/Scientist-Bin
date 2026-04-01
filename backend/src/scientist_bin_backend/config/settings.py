"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to the backend/ directory (3 levels up from this file)
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Central configuration for the Scientist-Bin backend.

    All fields use the ``SCIENTIST_BIN_`` env-var prefix except
    ``google_api_key`` which reads from the standard ``GOOGLE_API_KEY``.
    """

    model_config = SettingsConfigDict(
        env_prefix="SCIENTIST_BIN_",
        env_file=str(_ENV_FILE),
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

    # Sandbox / execution settings
    sandbox_timeout: int = 300  # seconds per code execution
    max_iterations: int = 5  # max generate-execute-analyze cycles
    sandbox_max_output_bytes: int = 1_000_000  # 1 MB stdout cap


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()  # type: ignore[call-arg]
