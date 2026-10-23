from __future__ import annotations

from datetime import date, time
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response

from app.config import Settings, get_settings
from app.domain.timing import parse_cutoff
from app.errors import InvalidParameterError
from app.schemas import (
    AccuracyOut,
    CutoffPreset,
    DecisionOut,
    ErrorOut,
    HealthOut,
    HorizonOut,
    MetaOut,
    VintagesOut,
)
from app.services import AnalysisService, format_cutoff

CACHE_HEADER = "public, max-age=300, s-maxage=86400"
CUTOFF_PATTERN = r"^\d{2}:\d{2}$"
ERROR_RESPONSES = {404: {"model": ErrorOut}, 422: {"model": ErrorOut}}

router = APIRouter(prefix="/api/v1", responses=ERROR_RESPONSES)


def get_service(request: Request) -> AnalysisService:
    state = request.app.state
    if getattr(state, "service", None) is None:
        state.service = state.service_factory()
    return state.service


def cutoff_param(
    settings: Annotated[Settings, Depends(get_settings)],
    cutoff: Annotated[
        str | None,
        Query(pattern=CUTOFF_PATTERN, description="Decision cutoff on the day before delivery, local HH:MM"),
    ] = None,
) -> time:
    if cutoff is None:
        return settings.default_cutoff
    try:
        return parse_cutoff(cutoff)
    except ValueError as exc:
        raise InvalidParameterError("cutoff must be a valid local time in HH:MM") from exc


ServiceDep = Annotated[AnalysisService, Depends(get_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
CutoffDep = Annotated[time, Depends(cutoff_param)]
DayQuery = Annotated[date, Query(alias="day", description="Delivery day, YYYY-MM-DD")]


def cacheable(response: Response) -> None:
    response.headers["Cache-Control"] = CACHE_HEADER


@router.get("/health", response_model=HealthOut)
def health(service: ServiceDep) -> HealthOut:
    return HealthOut(
        status="ok",
        actual_rows=len(service.dataset.actuals),
        forecast_rows=len(service.dataset.forecasts),
    )


@router.get("/meta", response_model=MetaOut)
def meta(service: ServiceDep, response: Response, settings: SettingsDep) -> MetaOut:
    cacheable(response)
    schedule = sorted(set(service.dataset.forecasts["publishTime"].dt.strftime("%H:%M")))
    return MetaOut(
        timezone=settings.timezone,
        decision_window_start=settings.decision_window_start,
        decision_window_end=settings.decision_window_end,
        delivery_days=service.delivery_days,
        default_cutoff=format_cutoff(settings.default_cutoff),
        cutoff_presets=[
            CutoffPreset(label="EPEX hourly", cutoff="09:20", description="EPEX GB day-ahead hourly auction"),
            CutoffPreset(
                label="N2EX hourly", cutoff="09:50", description="Nord Pool N2EX GB day-ahead auction"
            ),
            CutoffPreset(label="EPEX half-hourly", cutoff="15:30", description="EPEX GB 30-minute auction"),
        ],
        publish_schedule_utc=schedule,
        sources={"actuals": "Elexon BMRS FUELHH (fuelType WIND)", "forecasts": "Elexon BMRS WINDFOR"},
        error_convention="error = forecast - actual; positive means wind under-delivered against forecast",
    )


@router.get("/decision", response_model=DecisionOut)
def decision(service: ServiceDep, response: Response, day: DayQuery, cutoff: CutoffDep) -> DecisionOut:
    cacheable(response)
    return service.decision(day, cutoff)


@router.get("/accuracy", response_model=AccuracyOut)
def accuracy(service: ServiceDep, response: Response, cutoff: CutoffDep) -> AccuracyOut:
    cacheable(response)
    return service.accuracy(cutoff)


@router.get("/horizon", response_model=HorizonOut)
def horizon(service: ServiceDep, response: Response, cutoff: CutoffDep) -> HorizonOut:
    cacheable(response)
    return service.horizon(cutoff)


@router.get("/vintages", response_model=VintagesOut)
def vintages(service: ServiceDep, response: Response, day: DayQuery, cutoff: CutoffDep) -> VintagesOut:
    cacheable(response)
    return service.vintages(day, cutoff)
