from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def fetch(client: httpx.Client, dataset: str, params: dict[str, str]) -> list[dict]:
    response = client.get(f"{BASE_URL}/{dataset}/stream", params=params, timeout=120)
    response.raise_for_status()
    return response.json()


def daily_chunks(start: date, end: date, days: int) -> list[tuple[date, date]]:
    chunks = []
    cursor = start
    while cursor <= end:
        stop = min(cursor + timedelta(days=days - 1), end)
        chunks.append((cursor, stop))
        cursor = stop + timedelta(days=1)
    return chunks


def fetch_actuals(client: httpx.Client, start: date, end: date) -> list[tuple[str, int]]:
    rows: set[tuple[str, int]] = set()
    for lo, hi in daily_chunks(start, end, 7):
        records = fetch(
            client,
            "FUELHH",
            {"settlementDateFrom": lo.isoformat(), "settlementDateTo": hi.isoformat(), "fuelType": "WIND"},
        )
        rows.update(
            (r["startTime"], int(r["generation"]))
            for r in records
            if r.get("fuelType") == "WIND" and r.get("generation") is not None
        )
    return sorted(rows)


def fetch_forecasts(client: httpx.Client, start: date, end: date) -> list[tuple[str, str, int]]:
    rows: set[tuple[str, str, int]] = set()
    for lo, hi in daily_chunks(start, end, 7):
        records = fetch(
            client,
            "WINDFOR",
            {
                "publishDateTimeFrom": f"{lo.isoformat()}T00:00:00Z",
                "publishDateTimeTo": f"{(hi + timedelta(days=1)).isoformat()}T00:00:00Z",
            },
        )
        rows.update(
            (r["publishTime"], r["startTime"], int(r["generation"]))
            for r in records
            if r.get("generation") is not None
        )
    return sorted(rows)


def write_csv(path: Path, header: list[str], rows: list[tuple]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Elexon wind actuals and forecasts as CSV snapshots."
    )
    parser.add_argument("--actuals-from", type=date.fromisoformat, default=date(2025, 12, 31))
    parser.add_argument("--actuals-to", type=date.fromisoformat, default=date(2026, 2, 2))
    parser.add_argument("--forecasts-from", type=date.fromisoformat, default=date(2025, 12, 29))
    parser.add_argument("--forecasts-to", type=date.fromisoformat, default=date(2026, 2, 1))
    return parser.parse_args(argv)


def main(argv: list[str]) -> None:
    args = parse_args(argv)
    DATA_DIR.mkdir(exist_ok=True)
    with httpx.Client() as client:
        actuals = fetch_actuals(client, args.actuals_from, args.actuals_to)
        forecasts = fetch_forecasts(client, args.forecasts_from, args.forecasts_to)
    write_csv(DATA_DIR / "actuals.csv", ["startTime", "generation"], actuals)
    write_csv(DATA_DIR / "forecasts.csv", ["publishTime", "startTime", "generation"], forecasts)
    print(f"actuals={len(actuals)} forecasts={len(forecasts)} dir={DATA_DIR}")


if __name__ == "__main__":
    main(sys.argv[1:])
