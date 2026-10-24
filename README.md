# Windcast

Decision support for a UK utility buying power in the GB day-ahead market. Windcast shows the national wind generation forecast that was actually available when the purchase decision had to be made, and measures how accurate those forecasts were, so the team can size the volume it buys from other sources with the forecast error in mind.

**Live app:** : https://qzvtnm.vercel.app/

## What it does

The buying decision for delivery day **D** is made on **D-1**, before the auction gate closes. Elexon republishes the wind forecast several times a day, so the forecast that matters for each delivery hour is the **latest one published at or before the decision cutoff**. Windcast is built around that rule.

| View | Question it answers |
|---|---|
| **Decision day** | For a chosen delivery day and cutoff, which forecast did the buyer have, what range should they plan for, and how did the day turn out? Also shows every forecast publication for that day and which ones arrived too late. |
| **Forecast accuracy** | Across all January 2026 decisions: MAE, RMSE, bias, error distribution, error by day and by hour, and a comparison of auction cutoffs. |
| **Lead time** | How forecast error changes with the time between publication and delivery, with the buyer's decision window highlighted. |

### Key definitions

- **Scope:** purchase decisions made on 1–31 January 2026, which means delivery days **2 January – 1 February 2026**.
- **Cutoff:** a local UK time on D-1. Presets: EPEX hourly auction 09:20 (default), N2EX 09:50, EPEX half-hourly 15:30. Any time can be entered.
- **Forecast used:** for each delivery hour, the latest WINDFOR value with `publishTime <= cutoff`.
- **Actual:** FUELHH `WIND` generation. FUELHH is half-hourly and WINDFOR is hourly, so the two half-hours of each hour are averaged. Hours missing a half-hour are excluded rather than guessed.
- **Error:** `forecast − actual` in MW. Positive means wind came in below forecast, so the buyer was short.
- **Likely range:** the P10–P90 ratio of actual to forecast, taken only from delivery days whose outcome was known at the decision cutoff (D-2 and earlier). There is no look-ahead. Using a ratio lets the range scale with the forecast level.

## Headline findings (09:20 cutoff)

- Mean absolute error 2.0 GW (18% of mean output), RMSE 2.5 GW.
- Strong positive bias of +1.7 GW. The forecast was higher than outturn in 85% of hours, and the gap grows with wind level.
- Planning for wind 4.1 GW below the forecast would have covered the shortfall in 90% of hours.
- The bias persists even for forecasts made 0–6 hours ahead, which points to a systematic difference between the forecast and metered output (for example curtailment) rather than weather uncertainty alone.
- Elexon publishes at 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30 and 22:30 UTC. With a 09:20 gate closure the 09:30 forecast arrives ten minutes too late, so the 07:30 run is the one that drives decisions.

## How the dashboard answers the brief

### Requirement 1: understand the latest forecast available at decision time

| Element | Why it is there |
|---|---|
| Cutoff picker (EPEX 09:20, N2EX 09:50, EPEX 15:30, custom) | "Latest forecast available when deciding" depends on when the decision is made. Gate closure differs by auction, so the cutoff is an input rather than a hard-coded assumption. |
| Day stepper with arrow keys | Buyers review one delivery day at a time; stepping through days is the natural way to audit a month of decisions. |
| Decision callout | States the decision in plain words: delivery day, decision time, which publication was used and how far ahead it looked. Removes any doubt about which forecast is shown. |
| Forecast line with likely range | The forecast alone hides its uncertainty. The P10–P90 band shows the realistic spread, built only from information available at the cutoff. |
| Energy cards: forecast, prudent plan (P10), actual | Purchases are made in energy, not in instantaneous MW. The prudent plan converts the uncertainty into a volume the team can act on. |
| "Show actual generation" toggle | Lets the user first see exactly what the buyer saw, then reveal the outcome. Keeps decision-time information and hindsight clearly separate. |
| Forecast evolution chart | Shows every publication covering the day, marking which arrived before the cutoff and which arrived too late. Answers "would waiting have helped?" for a single day. |

### Requirement 2: evaluate forecast accuracy quantitatively

| Element | Why it is there |
|---|---|
| MAE and normalised MAE | Typical size of a miss, in GW and as a share of output, so it is easy to compare with portfolio size. |
| RMSE | Penalises large misses, which are the expensive ones for a buyer. |
| Bias and over-forecast share | Direction of the error. A buyer cares whether the forecast is systematically high (shortfall risk) or low (surplus), not only how big the error is. |
| P90 shortfall buffer | Turns the error distribution into a planning number: how much below the forecast to plan to be covered in 9 of 10 hours. |
| Error histogram | Shows the shape and skew of errors; colour separates shortfall from surplus. |
| Error by delivery day | Identifies the days where the forecast failed badly, for follow-up. |
| Error by hour of day | Shows which parts of the day need a larger buffer. |
| Cutoff comparison table | Quantifies whether buying at a later auction would reduce error. |
| Lead-time view | Shows how error grows with the time between publication and delivery, with the buyer's actual decision window highlighted. |

### Design decisions and trade-offs

| Decision | Alternative considered | Reason |
|---|---|---|
| Select the latest forecast per target hour, each with its own cutoff | One cutoff per calendar day applied to a block | Hours near midnight belong to different delivery days and so different cutoffs. Per-hour selection is always correct. |
| Delivery window 2 Jan – 1 Feb | Delivery days in January | The brief scopes *decisions* made in January. A decision on D-1 covers delivery on D. |
| Average two half-hours into an hourly actual | Compare only the :00 half-hour | Day-ahead hourly products cover the full hour, so the hourly mean is the matching quantity. Incomplete hours are dropped, not guessed. |
| Range from actual/forecast ratios | Fixed MW error quantiles | Error grows with wind level. A fixed band was too wide on calm days and too narrow on windy days. |
| Range from days up to D-2 only | All days in the month | Using later days would leak information the buyer did not have. A test enforces this. |
| nMAE instead of MAPE | MAPE | MAPE is unstable when actual output is near zero. |
| CSV snapshot of Elexon data | Live API calls per request | Deterministic, fast demo that does not depend on Elexon availability. Production would ingest on a schedule into a database. |
| Error defined as forecast − actual | actual − forecast | Positive error then means a shortfall, which is the risk the buyer manages. |

## Architecture

```
React (Vite, TypeScript)  ──HTTP──►  FastAPI  ──►  analysis (pandas)  ──►  CSV snapshot of Elexon data
  TanStack Query cache                /api/v1        pure functions          backend/data/*.csv
  URL-synced view state               validation     tested in isolation     refreshed by scripts/fetch_data.py
```

- **Snapshot data.** The app reads a committed snapshot of the two Elexon datasets, so the deployed demo is fast and deterministic, and doesn't depend on Elexon being reachable. `scripts/fetch_data.py` rebuilds the snapshot.
- **Layering.** `domain/` holds pure functions with no FastAPI code; `services.py` composes them and caches per cutoff; `api.py` handles HTTP, validation and caching headers; `schemas.py` defines the typed response contract.
- **API design.** Versioned under `/api/v1`, read-only `GET` endpoints, camelCase JSON, a consistent error envelope `{"error": {"code", "message"}}`, and OpenAPI docs at `/docs`.
- **Observability.** One JSON log line per request with a request ID, status and duration. Every response carries `X-Request-ID` and `Server-Timing` headers.
- **Frontend state.** Server state lives in TanStack Query, with adjacent days prefetched for instant stepping. View, day and cutoff live in the URL, so every screen is shareable and the back button works.

### API

| Endpoint | Description |
|---|---|
| `GET /api/v1/health` | Liveness and loaded row counts |
| `GET /api/v1/meta` | Delivery window, cutoff presets, publication schedule |
| `GET /api/v1/decision?day=YYYY-MM-DD&cutoff=HH:MM` | Forecast at decision time, actuals, likely range, energy totals |
| `GET /api/v1/vintages?day=YYYY-MM-DD&cutoff=HH:MM` | Every publication covering a day, flagged usable or late |
| `GET /api/v1/accuracy?cutoff=HH:MM` | Period metrics, quantiles, by-day, by-hour, histogram, series |
| `GET /api/v1/horizon?cutoff=HH:MM` | Error by lead time across all publications |

## Repository layout

```
.
├── api/index.py               Vercel serverless entrypoint wrapping the FastAPI app
├── backend/
│   ├── app/
│   │   ├── config.py          Settings (window, default cutoff, timezone), overridable via WINDCAST_* env vars
│   │   ├── data.py            CSV loading, cleaning and validation
│   │   ├── domain/
│   │   │   ├── timing.py      Cutoff, timezone and delivery-window rules
│   │   │   ├── selection.py   Decision-time forecast selection and hourly actuals
│   │   │   └── metrics.py     Error metrics, histogram, lead-time profile, likely range
│   │   ├── services.py        Composes the domain into API responses, cached per cutoff
│   │   ├── api.py             Routes, query validation, cache headers
│   │   ├── schemas.py         Pydantic response models (the API contract)
│   │   ├── errors.py          Error types and the JSON error envelope
│   │   ├── observability.py   JSON logging and request-ID / timing middleware
│   │   └── main.py            App factory
│   ├── data/                  Elexon snapshot: actuals.csv, forecasts.csv
│   ├── scripts/fetch_data.py  Rebuilds the snapshot from the Elexon BMRS API
│   ├── tests/                 pytest suite (unit and API)
│   ├── pyproject.toml, uv.lock
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/               Typed client, response types, query definitions
│   │   ├── state/             URL-synced view state
│   │   ├── lib/               Formatting helpers
│   │   ├── components/        Cards, stats, controls, loading and error states
│   │   ├── charts/            Recharts visualisations
│   │   ├── views/             Decision, Accuracy and Lead-time screens
│   │   └── App.tsx, main.tsx, styles.css
│   ├── nginx.conf, Dockerfile
│   └── package.json
├── docker-compose.yml         Runs api and web together
├── vercel.json                Static frontend plus Python function for /api
├── requirements.txt           Runtime dependencies for Vercel, exported from uv.lock
└── .github/workflows/ci.yml   Lint, type-check, tests, build and Docker smoke test
```

## Running locally

**Prerequisites:** Python 3.12 with [uv](https://docs.astral.sh/uv/), Node 22+.

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to port 8000. API docs are at http://localhost:8000/docs.

### With Docker

```bash
docker compose up --build
```

Open http://localhost:8080.

### Tests and checks

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run pytest --cov=app
cd frontend && npm run lint && npm run typecheck && npm test && npm run build
```

### Refreshing the data

```bash
cd backend && uv run --extra fetch python scripts/fetch_data.py
```

## Deployment

Vercel builds the frontend into static files and deploys `api/index.py` as a Python function. `vercel.json` routes `/api/*` to it and bundles `backend/app` and `backend/data` with the function. If dependencies change, regenerate `requirements.txt` with `uv export --no-dev --no-hashes --no-emit-project --no-header --no-annotate -o ../requirements.txt` from `backend/`. CI fails if it drifts from the lockfile.

## Limitations and next steps

- Data is a January 2026 snapshot. A production version would ingest new publications on a schedule and store them in a database.
- The likely range is empirical and unconditional. Conditioning it on forecast level, hour of day or lead time would tighten it.
- National wind only. Solar, demand and price data would turn this into a full net-position view.
- FUELHH covers metered transmission-connected wind. Embedded generation and curtailment volumes would help explain the bias.

## Use of AI tools

AI coding assistants were used to help with parts of the implementation and documentation. The design, analysis choices and final code were reviewed and are owned by the author.
