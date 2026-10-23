from __future__ import annotations

from dataclasses import asdict
from datetime import date, time, timedelta
from functools import cached_property
from threading import Lock

import pandas as pd

from app.config import Settings
from app.data import Dataset
from app.domain import metrics
from app.domain.selection import attach_actuals, decision_forecasts, forecast_vintages, hourly_actuals
from app.domain.timing import decision_cutoff_utc, delivery_days_for_decisions, local_dates, local_hours
from app.errors import NotFoundError
from app.schemas import (
    AccuracyOut,
    DaySummary,
    DecisionOut,
    DecisionPoint,
    EnergyTotals,
    HistogramBin,
    HorizonBucket,
    HorizonOut,
    HourSummary,
    SeriesPoint,
    SummaryOut,
    Vintage,
    VintagePoint,
    VintagesOut,
)


def summary_out(summary: metrics.Summary) -> SummaryOut:
    return SummaryOut(**asdict(summary))


def format_cutoff(cutoff: time) -> str:
    return cutoff.strftime("%H:%M")


def optional(value: float) -> float | None:
    return None if pd.isna(value) else float(value)


class AnalysisService:
    def __init__(self, dataset: Dataset, settings: Settings) -> None:
        self._dataset = dataset
        self._settings = settings
        self._joined_cache: dict[time, pd.DataFrame] = {}
        self._lock = Lock()

    @property
    def dataset(self) -> Dataset:
        return self._dataset

    @cached_property
    def delivery_days(self) -> list[date]:
        return delivery_days_for_decisions(
            self._settings.decision_window_start, self._settings.decision_window_end
        )

    @cached_property
    def actuals_hourly(self) -> pd.DataFrame:
        return hourly_actuals(self._dataset.actuals)

    @cached_property
    def forecast_days(self) -> pd.Series:
        return local_dates(self._dataset.forecasts["startTime"], self._settings.timezone)

    def require_delivery_day(self, day: date) -> date:
        if day not in self.delivery_days:
            first, last = self.delivery_days[0], self.delivery_days[-1]
            raise NotFoundError(f"delivery day must be between {first} and {last}")
        return day

    def joined(self, cutoff: time) -> pd.DataFrame:
        with self._lock:
            if cutoff not in self._joined_cache:
                selected = decision_forecasts(self._dataset.forecasts, cutoff, self._settings.timezone)
                self._joined_cache[cutoff] = attach_actuals(selected, self.actuals_hourly)
            return self._joined_cache[cutoff]

    def in_window(self, frame: pd.DataFrame) -> pd.DataFrame:
        return frame[frame["deliveryDay"].isin(set(self.delivery_days))]

    def decision(self, day: date, cutoff: time) -> DecisionOut:
        self.require_delivery_day(day)
        band, history_days = metrics.uncertainty_band(
            self.joined(cutoff), day, self._settings.min_history_days
        )
        if band.empty:
            raise NotFoundError(f"no forecast published before the cutoff covers {day}")
        band_available = bool(band["low"].notna().all())
        points = [
            DecisionPoint(
                time=row.startTime,
                forecast=float(row.forecast),
                actual=float(row.actual),
                error=float(row.error),
                publish_time=row.publishTime,
                horizon_hours=round(float(row.horizonHours), 2),
                low=optional(row.low),
                high=optional(row.high),
            )
            for row in band.itertuples()
        ]
        return DecisionOut(
            delivery_day=day,
            decision_day=day - timedelta(days=1),
            cutoff=format_cutoff(cutoff),
            cutoff_utc=decision_cutoff_utc(day, cutoff, self._settings.timezone),
            forecast_publish_times=sorted(set(band["publishTime"])),
            history_days=history_days,
            band_available=band_available,
            summary=summary_out(metrics.summarize(band)),
            energy=EnergyTotals(
                forecast_mwh=float(band["forecast"].sum()),
                actual_mwh=float(band["actual"].sum()),
                conservative_mwh=float(band["low"].sum()) if band_available else None,
            ),
            points=points,
        )

    def accuracy(self, cutoff: time) -> AccuracyOut:
        frame = self.in_window(self.joined(cutoff))
        hours = local_hours(frame["startTime"], self._settings.timezone)
        return AccuracyOut(
            cutoff=format_cutoff(cutoff),
            delivery_start=self.delivery_days[0],
            delivery_end=self.delivery_days[-1],
            summary=summary_out(metrics.summarize(frame)),
            error_quantiles=metrics.error_quantiles(frame),
            by_day=[
                DaySummary(delivery_day=day, summary=summary_out(s))
                for day, s in metrics.summarize_by(frame, frame["deliveryDay"])
            ],
            by_hour=[
                HourSummary(hour=int(hour), summary=summary_out(s))
                for hour, s in metrics.summarize_by(frame, hours)
            ],
            histogram=[HistogramBin(start=a, end=b, count=c) for a, b, c in metrics.error_histogram(frame)],
            series=[
                SeriesPoint(time=row.startTime, forecast=float(row.forecast), actual=float(row.actual))
                for row in frame.itertuples()
            ],
        )

    def horizon(self, cutoff: time) -> HorizonOut:
        decision_rows = self.in_window(self.joined(cutoff))
        buckets = metrics.horizon_profile(
            self._dataset.forecasts,
            self.actuals_hourly,
            set(self.delivery_days),
            self.forecast_days,
            self._settings.horizon_bucket_hours,
            self._settings.max_horizon_hours,
        )
        return HorizonOut(
            bucket_hours=self._settings.horizon_bucket_hours,
            decision_horizon_min=optional(decision_rows["horizonHours"].min()),
            decision_horizon_max=optional(decision_rows["horizonHours"].max()),
            buckets=[
                HorizonBucket(start_hours=lo, end_hours=hi, summary=summary_out(s)) for lo, hi, s in buckets
            ],
        )

    def vintages(self, day: date, cutoff: time) -> VintagesOut:
        self.require_delivery_day(day)
        tz = self._settings.timezone
        cutoff_utc = decision_cutoff_utc(day, cutoff, tz)
        earliest = decision_cutoff_utc(day, time(0, 0), tz) - timedelta(days=1)
        frame = forecast_vintages(self._dataset.forecasts, day, tz)
        frame = frame[frame["publishTime"] >= earliest]
        actuals = self.actuals_hourly[local_dates(self.actuals_hourly["startTime"], tz) == day]
        return VintagesOut(
            delivery_day=day,
            cutoff=format_cutoff(cutoff),
            actuals=[
                VintagePoint(time=r.startTime, generation=float(r.actual)) for r in actuals.itertuples()
            ],
            vintages=[
                Vintage(
                    publish_time=published,
                    usable_for_decision=bool(published <= cutoff_utc),
                    points=[
                        VintagePoint(time=r.startTime, generation=float(r.generation))
                        for r in rows.itertuples()
                    ],
                )
                for published, rows in frame.groupby("publishTime", sort=True)
            ],
        )
