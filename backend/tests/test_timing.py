from __future__ import annotations

from datetime import date, time

import pandas as pd
import pytest

from app.domain.timing import decision_cutoff_utc, delivery_days_for_decisions, local_dates, parse_cutoff

LONDON = "Europe/London"


def test_cutoff_is_on_the_day_before_delivery_in_winter() -> None:
    assert decision_cutoff_utc(date(2026, 1, 15), time(9, 20), LONDON) == pd.Timestamp("2026-01-14T09:20:00Z")


def test_cutoff_respects_british_summer_time() -> None:
    assert decision_cutoff_utc(date(2026, 7, 15), time(9, 20), LONDON) == pd.Timestamp("2026-07-14T08:20:00Z")


def test_cutoff_on_the_day_clocks_go_forward() -> None:
    assert decision_cutoff_utc(date(2026, 3, 30), time(9, 20), LONDON) == pd.Timestamp("2026-03-29T08:20:00Z")


def test_january_decisions_cover_second_of_january_to_first_of_february() -> None:
    days = delivery_days_for_decisions(date(2026, 1, 1), date(2026, 1, 31))
    assert days[0] == date(2026, 1, 2)
    assert days[-1] == date(2026, 2, 1)
    assert len(days) == 31


def test_local_dates_use_london_calendar_in_summer() -> None:
    stamps = pd.Series(pd.to_datetime(["2026-07-01T23:30:00Z"], utc=True))
    assert local_dates(stamps, LONDON).iloc[0] == date(2026, 7, 2)


@pytest.mark.parametrize("value", ["9:20", "09:2", "0920", "aa:bb", "24:00", "09:60"])
def test_parse_cutoff_rejects_malformed_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_cutoff(value)


def test_parse_cutoff_accepts_valid_value() -> None:
    assert parse_cutoff("15:30") == time(15, 30)
