from __future__ import annotations

from datetime import date, time

import pandas as pd

from app.data import clean_actuals, clean_forecasts
from app.domain.selection import attach_actuals, decision_forecasts, hourly_actuals
from tests.conftest import actual_frame, forecast_frame, utc

LONDON = "Europe/London"
CUTOFF = time(9, 20)


def test_latest_forecast_before_cutoff_wins() -> None:
    forecasts = forecast_frame(
        [
            ("2026-01-14T02:30Z", "2026-01-15T12:00Z", 100),
            ("2026-01-14T07:30Z", "2026-01-15T12:00Z", 200),
            ("2026-01-14T09:30Z", "2026-01-15T12:00Z", 999),
        ]
    )
    selected = decision_forecasts(forecasts, CUTOFF, LONDON)
    assert selected["forecast"].tolist() == [200]
    assert selected["publishTime"].iloc[0] == utc("2026-01-14T07:30")


def test_forecast_published_exactly_at_cutoff_is_usable() -> None:
    forecasts = forecast_frame([("2026-01-14T09:20Z", "2026-01-15T12:00Z", 300)])
    assert decision_forecasts(forecasts, CUTOFF, LONDON)["forecast"].tolist() == [300]


def test_hours_with_only_late_forecasts_are_dropped() -> None:
    forecasts = forecast_frame([("2026-01-14T11:30Z", "2026-01-15T12:00Z", 300)])
    assert decision_forecasts(forecasts, CUTOFF, LONDON).empty


def test_each_delivery_day_uses_its_own_cutoff() -> None:
    forecasts = forecast_frame(
        [
            ("2026-01-14T07:30Z", "2026-01-15T23:00Z", 1),
            ("2026-01-15T07:30Z", "2026-01-15T23:00Z", 2),
            ("2026-01-15T07:30Z", "2026-01-16T00:00Z", 3),
        ]
    )
    selected = decision_forecasts(forecasts, CUTOFF, LONDON).set_index("startTime")
    assert selected.loc[utc("2026-01-15T23:00"), "forecast"] == 1
    assert selected.loc[utc("2026-01-16T00:00"), "forecast"] == 3


def test_horizon_is_hours_between_publish_and_target() -> None:
    forecasts = forecast_frame([("2026-01-14T07:30Z", "2026-01-15T00:00Z", 1)])
    assert decision_forecasts(forecasts, CUTOFF, LONDON)["horizonHours"].iloc[0] == 16.5


def test_hourly_actuals_average_both_half_hours() -> None:
    actuals = actual_frame([("2026-01-15T12:00Z", 100), ("2026-01-15T12:30Z", 300)])
    hourly = hourly_actuals(actuals)
    assert hourly["actual"].tolist() == [200]
    assert hourly["startTime"].iloc[0] == utc("2026-01-15T12:00")


def test_hourly_actuals_skip_incomplete_hours() -> None:
    actuals = actual_frame([("2026-01-15T12:00Z", 100), ("2026-01-15T13:00Z", 50), ("2026-01-15T13:30Z", 70)])
    assert hourly_actuals(actuals)["actual"].tolist() == [60]


def test_error_is_forecast_minus_actual() -> None:
    forecasts = decision_forecasts(
        forecast_frame([("2026-01-14T07:30Z", "2026-01-15T12:00Z", 500)]), CUTOFF, LONDON
    )
    actuals = hourly_actuals(actual_frame([("2026-01-15T12:00Z", 400), ("2026-01-15T12:30Z", 400)]))
    joined = attach_actuals(forecasts, actuals)
    assert joined["error"].tolist() == [100]
    assert joined["deliveryDay"].iloc[0] == date(2026, 1, 15)


def test_cleaning_drops_past_targets_duplicates_and_negatives() -> None:
    raw = pd.DataFrame(
        {
            "publishTime": [
                "2026-01-14T07:30Z",
                "2026-01-14T07:30Z",
                "2026-01-14T07:30Z",
                "2026-01-14T07:30Z",
            ],
            "startTime": ["2026-01-14T06:00Z", "2026-01-15T00:00Z", "2026-01-15T00:00Z", "2026-01-15T01:00Z"],
            "generation": [10, 20, 25, -5],
        }
    )
    cleaned = clean_forecasts(raw)
    assert cleaned["generation"].tolist() == [25]


def test_cleaning_actuals_parses_and_dedupes() -> None:
    raw = pd.DataFrame(
        {
            "startTime": ["2026-01-15T00:30Z", "2026-01-15T00:00Z", "2026-01-15T00:30Z"],
            "generation": ["1", "x", "3"],
        }
    )
    cleaned = clean_actuals(raw)
    assert cleaned["generation"].tolist() == [3]
