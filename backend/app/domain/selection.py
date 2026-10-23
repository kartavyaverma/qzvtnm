from __future__ import annotations

from datetime import date, time

import pandas as pd

from app.domain.timing import decision_cutoff_utc, local_dates

HALF_HOURS_PER_HOUR = 2


def hourly_actuals(actuals: pd.DataFrame) -> pd.DataFrame:
    hours = actuals["startTime"].dt.floor("h")
    grouped = actuals.groupby(hours)["generation"].agg(["mean", "count"])
    complete = grouped[grouped["count"] == HALF_HOURS_PER_HOUR]
    return (
        complete["mean"]
        .rename("actual")
        .rename_axis("startTime")
        .reset_index()
        .sort_values("startTime", ignore_index=True)
    )


def decision_forecasts(forecasts: pd.DataFrame, cutoff: time, timezone: str) -> pd.DataFrame:
    frame = forecasts.copy()
    frame["deliveryDay"] = local_dates(frame["startTime"], timezone)
    cutoffs = {day: decision_cutoff_utc(day, cutoff, timezone) for day in frame["deliveryDay"].unique()}
    frame["cutoff"] = frame["deliveryDay"].map(cutoffs)
    eligible = frame[frame["publishTime"] <= frame["cutoff"]]
    latest = eligible.sort_values("publishTime").groupby("startTime", as_index=False).last()
    latest = latest.rename(columns={"generation": "forecast"})
    latest["horizonHours"] = (latest["startTime"] - latest["publishTime"]).dt.total_seconds() / 3600
    columns = ["startTime", "deliveryDay", "publishTime", "cutoff", "forecast", "horizonHours"]
    return latest[columns].sort_values("startTime", ignore_index=True)


def attach_actuals(forecasts: pd.DataFrame, actuals_hourly: pd.DataFrame) -> pd.DataFrame:
    joined = forecasts.merge(actuals_hourly, on="startTime", how="inner")
    joined["error"] = joined["forecast"] - joined["actual"]
    return joined


def forecast_vintages(forecasts: pd.DataFrame, delivery_day: date, timezone: str) -> pd.DataFrame:
    days = local_dates(forecasts["startTime"], timezone)
    return forecasts[days == delivery_day].sort_values(["publishTime", "startTime"], ignore_index=True)
