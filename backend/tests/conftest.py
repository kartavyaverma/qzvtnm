from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.config import BACKEND_DIR, Settings
from app.main import create_app


def utc(value: str) -> pd.Timestamp:
    return pd.Timestamp(value, tz="UTC")


def forecast_frame(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=["publishTime", "startTime", "generation"])
    frame["publishTime"] = pd.to_datetime(frame["publishTime"], utc=True)
    frame["startTime"] = pd.to_datetime(frame["startTime"], utc=True)
    return frame


def actual_frame(rows: list[tuple[str, float]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=["startTime", "generation"])
    frame["startTime"] = pd.to_datetime(frame["startTime"], utc=True)
    return frame


@pytest.fixture(scope="session")
def real_client() -> Iterator[TestClient]:
    settings = Settings(data_dir=BACKEND_DIR / "data", log_level="WARNING")
    with TestClient(create_app(settings)) as client:
        yield client


def write_snapshot(directory: Path, actuals: pd.DataFrame, forecasts: pd.DataFrame) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    actuals.to_csv(directory / "actuals.csv", index=False)
    forecasts.to_csv(directory / "forecasts.csv", index=False)
    return directory
