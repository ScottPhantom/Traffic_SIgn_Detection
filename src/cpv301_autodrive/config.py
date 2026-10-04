from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    model_path: Path = PROJECT_ROOT / "models" / "VGG16_model.h5"
    confidence_threshold: float = 0.50

    model_config = SettingsConfigDict(
        env_prefix="CPV301_",
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )

    @field_validator("model_path", mode="after")
    @classmethod
    def resolve_model_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else PROJECT_ROOT / value

    @field_validator("confidence_threshold")
    @classmethod
    def validate_threshold(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("confidence_threshold must be between 0 and 1")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
