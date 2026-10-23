from __future__ import annotations

from datetime import date, time
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WINDCAST_", env_file=".env", extra="ignore")

    data_dir: Path = BACKEND_DIR / "data"
    timezone: str = "Europe/London"
    decision_window_start: date = date(2026, 1, 1)
    decision_window_end: date = date(2026, 1, 31)
    default_cutoff: time = time(9, 20)
    min_history_days: int = Field(default=2, ge=1)
    horizon_bucket_hours: int = Field(default=6, ge=1)
    max_horizon_hours: int = Field(default=66, ge=1)
    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
