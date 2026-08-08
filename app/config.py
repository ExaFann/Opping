from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Opping API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./opping.db"
    upload_dir: Path = Path("./uploads")
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    ai_provider: Literal["auto", "gemini", "stub"] = "auto"
    gemini_api_key: str | None = Field(default=None, repr=False)
    gemini_model: str = "gemini-3.6-flash"

    max_images_per_listing: int = Field(default=5, ge=1, le=20)
    max_image_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

