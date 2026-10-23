from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd


def decision_cutoff_utc(delivery_day: date, cutoff: time, timezone: str) -> pd.Timestamp:
    local = datetime.combine(delivery_day - timedelta(days=1), cutoff, tzinfo=ZoneInfo(timezone))
    return pd.Timestamp(local).tz_convert("UTC")


def local_dates(timestamps: pd.Series, timezone: str) -> pd.Series:
    return timestamps.dt.tz_convert(timezone).dt.date


def local_hours(timestamps: pd.Series, timezone: str) -> pd.Series:
    return timestamps.dt.tz_convert(timezone).dt.hour


def delivery_days_for_decisions(first_decision: date, last_decision: date) -> list[date]:
    span = (last_decision - first_decision).days
    return [first_decision + timedelta(days=offset + 1) for offset in range(span + 1)]


def parse_cutoff(value: str) -> time:
    hours, minutes = value.split(":")
    if len(hours) != 2 or len(minutes) != 2:
        raise ValueError("cutoff must use HH:MM")
    return time(int(hours), int(minutes))
