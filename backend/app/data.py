from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

ACTUAL_COLUMNS = ["startTime", "generation"]
FORECAST_COLUMNS = ["publishTime", "startTime", "generation"]


class DataValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Dataset:
    actuals: pd.DataFrame
    forecasts: pd.DataFrame


def _require_columns(frame: pd.DataFrame, columns: list[str], name: str) -> None:
    missing = set(columns) - set(frame.columns)
    if missing:
        raise DataValidationError(f"{name} is missing columns: {sorted(missing)}")


def _to_utc(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True)


def clean_actuals(raw: pd.DataFrame) -> pd.DataFrame:
    _require_columns(raw, ACTUAL_COLUMNS, "actuals")
    frame = raw[ACTUAL_COLUMNS].copy()
    frame["startTime"] = _to_utc(frame["startTime"])
    frame["generation"] = pd.to_numeric(frame["generation"], errors="coerce")
    frame = frame.dropna().query("generation >= 0")
    frame = frame.drop_duplicates("startTime", keep="last")
    return frame.sort_values("startTime").reset_index(drop=True)


def clean_forecasts(raw: pd.DataFrame) -> pd.DataFrame:
    _require_columns(raw, FORECAST_COLUMNS, "forecasts")
    frame = raw[FORECAST_COLUMNS].copy()
    frame["publishTime"] = _to_utc(frame["publishTime"])
    frame["startTime"] = _to_utc(frame["startTime"])
    frame["generation"] = pd.to_numeric(frame["generation"], errors="coerce")
    frame = frame.dropna().query("generation >= 0")
    frame = frame[frame["startTime"] > frame["publishTime"]]
    frame = frame.drop_duplicates(["publishTime", "startTime"], keep="last")
    return frame.sort_values(["startTime", "publishTime"]).reset_index(drop=True)


def load_dataset(data_dir: Path) -> Dataset:
    actuals = clean_actuals(pd.read_csv(data_dir / "actuals.csv"))
    forecasts = clean_forecasts(pd.read_csv(data_dir / "forecasts.csv"))
    if actuals.empty or forecasts.empty:
        raise DataValidationError(f"no usable rows in {data_dir}")
    return Dataset(actuals=actuals, forecasts=forecasts)


@lru_cache(maxsize=4)
def cached_dataset(data_dir: Path) -> Dataset:
    return load_dataset(data_dir)
