from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.conftest import actual_frame, forecast_frame, write_snapshot


def test_health_reports_loaded_rows(real_client: TestClient) -> None:
    body = real_client.get("/api/v1/health").json()
    assert body["status"] == "ok"
    assert body["actualRows"] > 0
    assert body["forecastRows"] > 0


def test_meta_exposes_delivery_window(real_client: TestClient) -> None:
    body = real_client.get("/api/v1/meta").json()
    assert body["deliveryDays"][0] == "2026-01-02"
    assert body["deliveryDays"][-1] == "2026-02-01"
    assert body["defaultCutoff"] == "09:20"


def test_decision_never_uses_forecasts_published_after_cutoff(real_client: TestClient) -> None:
    body = real_client.get("/api/v1/decision", params={"day": "2026-01-15", "cutoff": "09:20"}).json()
    assert body["cutoffUtc"] == "2026-01-14T09:20:00Z"
    assert len(body["points"]) == 24
    assert all(p <= body["cutoffUtc"] for p in body["forecastPublishTimes"])


def test_later_cutoff_can_use_a_newer_forecast(real_client: TestClient) -> None:
    early = real_client.get("/api/v1/decision", params={"day": "2026-01-15", "cutoff": "09:20"}).json()
    late = real_client.get("/api/v1/decision", params={"day": "2026-01-15", "cutoff": "15:30"}).json()
    assert max(late["forecastPublishTimes"]) > max(early["forecastPublishTimes"])


def test_accuracy_covers_every_hour_of_the_window(real_client: TestClient) -> None:
    body = real_client.get("/api/v1/accuracy").json()
    assert body["deliveryStart"] == "2026-01-02"
    assert body["summary"]["count"] == 31 * 24
    assert len(body["byDay"]) == 31
    assert len(body["byHour"]) == 24


def test_horizon_buckets_are_ordered(real_client: TestClient) -> None:
    body = real_client.get("/api/v1/horizon").json()
    starts = [b["startHours"] for b in body["buckets"]]
    assert starts == sorted(starts)
    assert body["decisionHorizonMin"] < body["decisionHorizonMax"]


def test_vintages_flag_usable_publications(real_client: TestClient) -> None:
    body = real_client.get("/api/v1/vintages", params={"day": "2026-01-15"}).json()
    flags = {v["publishTime"]: v["usableForDecision"] for v in body["vintages"]}
    assert flags["2026-01-14T07:30:00Z"] is True
    assert flags["2026-01-14T09:30:00Z"] is False


@pytest.mark.parametrize(
    ("params", "status", "code"),
    [
        ({"day": "2026-01-01"}, 404, "not_found"),
        ({"day": "2026-02-02"}, 404, "not_found"),
        ({"day": "not-a-date"}, 422, "invalid_parameter"),
        ({}, 422, "invalid_parameter"),
        ({"day": "2026-01-15", "cutoff": "25:00"}, 422, "invalid_parameter"),
        ({"day": "2026-01-15", "cutoff": "9:20"}, 422, "invalid_parameter"),
    ],
)
def test_bad_requests_return_structured_errors(
    real_client: TestClient, params: dict[str, str], status: int, code: str
) -> None:
    response = real_client.get("/api/v1/decision", params=params)
    assert response.status_code == status
    assert response.json()["error"]["code"] == code


def test_responses_carry_request_id_and_cache_headers(real_client: TestClient) -> None:
    response = real_client.get("/api/v1/meta", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"
    assert "max-age" in response.headers["Cache-Control"]
    assert response.headers["Server-Timing"].startswith("app;dur=")


def test_day_with_no_eligible_forecast_returns_not_found(tmp_path: Path) -> None:
    actuals = actual_frame([("2026-01-15T12:00Z", 10), ("2026-01-15T12:30Z", 10)])
    forecasts = forecast_frame([("2026-01-15T11:30Z", "2026-01-15T12:00Z", 10)])
    settings = Settings(data_dir=write_snapshot(tmp_path, actuals, forecasts), log_level="WARNING")
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/decision", params={"day": "2026-01-15"})
    assert response.status_code == 404
