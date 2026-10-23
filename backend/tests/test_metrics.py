from __future__ import annotations

import math
from datetime import date, timedelta

import pandas as pd
import pytest

from app.domain import metrics


def joined_frame(errors_by_day: dict[date, list[float]], forecast: float = 1000.0) -> pd.DataFrame:
    rows = [
        {"deliveryDay": day, "forecast": forecast, "actual": forecast - e, "error": e}
        for day, errors in errors_by_day.items()
        for e in errors
    ]
    return pd.DataFrame(rows)


def test_summary_of_known_errors() -> None:
    frame = joined_frame({date(2026, 1, 2): [100, -100, 300, -300]})
    summary = metrics.summarize(frame)
    assert summary.count == 4
    assert summary.mae == 200
    assert summary.bias == 0
    assert summary.rmse == pytest.approx(math.sqrt((100**2 + 300**2) / 2))
    assert summary.over_forecast_share_pct == 50
    assert summary.max_over_forecast == 300
    assert summary.max_under_forecast == -300


def test_summary_of_empty_frame_has_no_values() -> None:
    summary = metrics.summarize(pd.DataFrame(columns=["forecast", "actual", "error"]))
    assert summary.count == 0
    assert summary.mae is None


def test_nmae_is_undefined_when_actual_is_zero() -> None:
    frame = pd.DataFrame({"forecast": [10.0], "actual": [0.0], "error": [10.0]})
    assert metrics.summarize(frame).nmae_pct is None


def test_histogram_counts_every_point() -> None:
    frame = joined_frame({date(2026, 1, 2): [-700, -10, 0, 20, 1200]})
    bins = metrics.error_histogram(frame, bin_width=500)
    assert sum(count for _, _, count in bins) == 5
    assert bins[0][0] == -1000


def test_histogram_handles_constant_errors() -> None:
    frame = joined_frame({date(2026, 1, 2): [0, 0, 0]})
    assert sum(count for _, _, count in metrics.error_histogram(frame)) == 3


def test_band_uses_only_days_known_at_decision_time() -> None:
    target = date(2026, 1, 10)
    history = {target - timedelta(days=n): [100.0] * 4 for n in (2, 3)}
    leak = {target - timedelta(days=1): [99999.0] * 4, target: [5000.0] * 4}
    band, history_days = metrics.uncertainty_band(
        joined_frame({**history, **leak}), target, min_history_days=2
    )
    assert history_days == 2
    assert band["low"].tolist() == [900.0] * 4
    assert band["high"].tolist() == [900.0] * 4


def test_band_is_missing_without_enough_history() -> None:
    target = date(2026, 1, 10)
    frame = joined_frame({target - timedelta(days=2): [1.0], target: [1.0]})
    band, history_days = metrics.uncertainty_band(frame, target, min_history_days=2)
    assert history_days == 1
    assert band["low"].isna().all()


def test_band_never_goes_below_zero() -> None:
    target = date(2026, 1, 10)
    frame = joined_frame({target - timedelta(days=d): [5000.0] for d in (2, 3)} | {target: [0.0]})
    band, _ = metrics.uncertainty_band(frame, target, min_history_days=2)
    assert band["low"].iloc[0] == 0
