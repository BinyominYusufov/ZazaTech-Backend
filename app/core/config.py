"""Application settings loaded from environment / .env via pydantic-settings."""

from __future__ import annotations

import json
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./zazetech.db"
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 60
    # NoDecode -> pydantic-settings hands us the raw env string instead of
    # trying to JSON-decode it, so we can accept both JSON and CSV forms.
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    NODE_ENV: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_origins(cls, value: object) -> list[str]:
        """Accept a JSON array (`["a","b"]`) or a comma-separated string."""
        if value is None or value == "":
            return ["http://localhost:3000"]
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [o.strip() for o in stripped.split(",") if o.strip()]
        if isinstance(value, (list, tuple)):
            return [str(o) for o in value]
        raise ValueError("ALLOWED_ORIGINS must be a list or a string")

    @property
    def is_production(self) -> bool:
        return self.NODE_ENV.lower() == "production"


settings = Settings()
