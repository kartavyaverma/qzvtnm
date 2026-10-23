from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

ERROR_QUANTILES = (0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95)


@dataclass(frozen=True)
class Summary:
    count: int
    mae: float | None
    rmse: float | None
    bias: float | None
    nmae_pct: float | None
    p50_error: float | None
    p90_error: float | None
    p95_abs_error: float | None
    max_over_forecast: float | None
    max_under_forecast: float | None
    over_forecast_share_pct: float | None
    mean_actual: float | None
    mean_forecast: float | None


EMPTY_SUMMARY = Summary(0, *([None] * 12))


def summarize(frame: pd.DataFrame) -> Summary:
    if frame.empty:
        return EMPTY_SUMMARY
    error = frame["error"]
    absolute = error.abs()
    mean_actual = float(frame["actual"].mean())
    mae = float(absolute.mean())
    return Summary(
        count=len(frame),
        mae=mae,
        rmse=float(np.sqrt((error**2).mean())),
        bias=float(error.mean()),
        nmae_pct=mae / mean_actual * 100 if mean_actual > 0 else None,
        p50_error=float(error.quantile(0.5)),
        p90_error=float(error.quantile(0.9)),
        p95_abs_error=float(absolute.quantile(0.95)),
        max_over_forecast=float(error.max()),
        max_under_forecast=float(error.min()),
        over_forecast_share_pct=float((error > 0).mean() * 100),
        mean_actual=mean_actual,
        mean_forecast=float(frame["forecast"].mean()),
    )


def error_quantiles(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {}
    values = frame["error"].quantile(list(ERROR_QUANTILES))
    return {f"p{round(q * 100)}": float(v) for q, v in values.items()}


def summarize_by(frame: pd.DataFrame, key: pd.Series) -> list[tuple[Hashable, Summary]]:
    return [(group, summarize(rows)) for group, rows in frame.groupby(key, sort=True)]


def error_histogram(frame: pd.DataFrame, bin_width: float = 500.0) -> list[tuple[float, float, int]]:
    if frame.empty:
        return []
    low = np.floor(frame["error"].min() / bin_width) * bin_width
    high = np.ceil(frame["error"].max() / bin_width) * bin_width
    edges = np.arange(low, high + bin_width, bin_width)
    if len(edges) < 2:
        edges = np.array([low, low + bin_width])
    counts, _ = np.histogram(frame["error"], bins=edges)
    return [(float(a), float(b), int(c)) for a, b, c in zip(edges[:-1], edges[1:], counts, strict=True)]


def horizon_profile(
    forecasts: pd.DataFrame,
    actuals_hourly: pd.DataFrame,
    delivery_days: set[date],
    days_of: pd.Series,
    bucket_hours: int,
    max_hours: int,
) -> list[tuple[int, int, Summary]]:
    frame = forecasts.assign(
        horizonHours=(forecasts["startTime"] - forecasts["publishTime"]).dt.total_seconds() / 3600
    )
    frame = frame[days_of.isin(delivery_days) & (frame["horizonHours"] < max_hours)]
    frame = frame.rename(columns={"generation": "forecast"}).merge(actuals_hourly, on="startTime")
    frame["error"] = frame["forecast"] - frame["actual"]
    buckets = (frame["horizonHours"] // bucket_hours).astype(int)
    return [
        (int(b) * bucket_hours, (int(b) + 1) * bucket_hours, summary)
        for b, summary in summarize_by(frame, buckets)
    ]


def uncertainty_band(
    joined: pd.DataFrame,
    delivery_day: date,
    min_history_days: int,
    quantiles: tuple[float, float] = (0.1, 0.9),
) -> tuple[pd.DataFrame, int]:
    latest_known_day = delivery_day - timedelta(days=2)
    history = joined[joined["deliveryDay"] <= latest_known_day]
    target = joined[joined["deliveryDay"] == delivery_day].copy()
    history_days = int(history["deliveryDay"].nunique())
    if history_days < min_history_days:
        target["low"] = np.nan
        target["high"] = np.nan
        return target, history_days
    usable = history[history["forecast"] > 0]
    ratios = usable["actual"] / usable["forecast"]
    low_ratio, high_ratio = ratios.quantile(list(quantiles))
    target["low"] = (target["forecast"] * low_ratio).clip(lower=0)
    target["high"] = (target["forecast"] * high_ratio).clip(lower=0)
    return target, history_days
