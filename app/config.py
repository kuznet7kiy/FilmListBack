"""Application settings, read from the environment and .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    mongodb_uri: str = ""
    mongodb_db: str = "movie_library"
    mongodb_collection: str = "movies"

    data_dir: Path = Path("data")
    media_dir: Path = Path("media")

    max_upload_bytes: int = 5 * 1024 * 1024
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )

    @field_validator("data_dir", "media_dir", mode="after")
    @classmethod
    def _absolutize(cls, value: Path) -> Path:
        """Resolve relative paths against backend/, not the current working directory."""
        return value if value.is_absolute() else BASE_DIR / value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def use_mongo(self) -> bool:
        return bool(self.mongodb_uri.strip())

    @property
    def movies_file(self) -> Path:
        return self.data_dir / "movies.json"

    @property
    def covers_dir(self) -> Path:
        return self.media_dir / "covers"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
