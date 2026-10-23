from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, frozen=True)


class SummaryOut(ApiModel):
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


class HealthOut(ApiModel):
    status: str
    actual_rows: int
    forecast_rows: int


class CutoffPreset(ApiModel):
    label: str
    cutoff: str
    description: str


class MetaOut(ApiModel):
    timezone: str
    decision_window_start: date
    decision_window_end: date
    delivery_days: list[date]
    default_cutoff: str
    cutoff_presets: list[CutoffPreset]
    publish_schedule_utc: list[str]
    sources: dict[str, str]
    error_convention: str


class DecisionPoint(ApiModel):
    time: datetime
    forecast: float
    actual: float
    error: float
    publish_time: datetime
    horizon_hours: float
    low: float | None
    high: float | None


class EnergyTotals(ApiModel):
    forecast_mwh: float
    actual_mwh: float
    conservative_mwh: float | None


class DecisionOut(ApiModel):
    delivery_day: date
    decision_day: date
    cutoff: str
    cutoff_utc: datetime
    forecast_publish_times: list[datetime]
    history_days: int
    band_available: bool
    summary: SummaryOut
    energy: EnergyTotals
    points: list[DecisionPoint]


class DaySummary(ApiModel):
    delivery_day: date
    summary: SummaryOut


class HourSummary(ApiModel):
    hour: int
    summary: SummaryOut


class HistogramBin(ApiModel):
    start: float
    end: float
    count: int


class SeriesPoint(ApiModel):
    time: datetime
    forecast: float
    actual: float


class AccuracyOut(ApiModel):
    cutoff: str
    delivery_start: date
    delivery_end: date
    summary: SummaryOut
    error_quantiles: dict[str, float]
    by_day: list[DaySummary]
    by_hour: list[HourSummary]
    histogram: list[HistogramBin]
    series: list[SeriesPoint]


class HorizonBucket(ApiModel):
    start_hours: int
    end_hours: int
    summary: SummaryOut


class HorizonOut(ApiModel):
    bucket_hours: int
    decision_horizon_min: float | None
    decision_horizon_max: float | None
    buckets: list[HorizonBucket]


class VintagePoint(ApiModel):
    time: datetime
    generation: float


class Vintage(ApiModel):
    publish_time: datetime
    usable_for_decision: bool
    points: list[VintagePoint]


class VintagesOut(ApiModel):
    delivery_day: date
    cutoff: str
    actuals: list[VintagePoint]
    vintages: list[Vintage]


class ErrorBody(ApiModel):
    code: str
    message: str


class ErrorOut(ApiModel):
    error: ErrorBody
