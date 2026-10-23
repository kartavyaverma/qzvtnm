from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

REQUEST_ID_HEADER = "X-Request-ID"
logger = logging.getLogger("windcast.request")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"level": record.levelname, "logger": record.name, "message": record.getMessage()}
        payload.update(getattr(record, "fields", {}))
        return json.dumps(payload)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("windcast")
    root.handlers = [handler]
    root.setLevel(level)
    root.propagate = False


def install_request_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request failed",
                extra={"fields": {"requestId": request_id, "path": request.url.path}},
            )
            raise
        duration_ms = (time.perf_counter() - started) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers["Server-Timing"] = f"app;dur={duration_ms:.1f}"
        logger.info(
            "request",
            extra={
                "fields": {
                    "requestId": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.url.query),
                    "status": response.status_code,
                    "durationMs": round(duration_ms, 1),
                }
            },
        )
        return response
