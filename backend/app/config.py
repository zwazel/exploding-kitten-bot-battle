"""Application configuration management."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    database_url: str = Field(
        default="postgresql+psycopg2://exploding:exploding@localhost:5432/exploding",
        description="SQLAlchemy database URL.",
    )
    secret_key: str = Field(
        default="change-me",
        description="Secret key for signing JWT tokens.",
    )
    access_token_expire_minutes: int = Field(default=120, ge=5, description="JWT expiry.")
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Origins allowed for CORS requests.",
    )
    storage_root: Path = Field(
        default=Path("backend/storage"),
        description="Root directory for uploaded bots and replay files.",
    )
    builtin_bots_directory: Path = Field(
        default=Path("bots"),
        description="Directory containing built-in bots packaged with the project.",
    )


    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    model_config = ConfigDict(env_file=".env", env_prefix="ARENA_", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    settings = Settings()
    project_root = Path(__file__).resolve().parents[2]
    if not settings.builtin_bots_directory.is_absolute():
        settings.builtin_bots_directory = (project_root / settings.builtin_bots_directory).resolve()
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    (settings.storage_root / "bots").mkdir(parents=True, exist_ok=True)
    (settings.storage_root / "replays").mkdir(parents=True, exist_ok=True)
    return settings


__all__ = ["Settings", "get_settings"]
