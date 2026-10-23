from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api import router
from app.config import Settings, get_settings
from app.data import cached_dataset
from app.errors import register_error_handlers
from app.observability import configure_logging, install_request_logging
from app.services import AnalysisService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    def build_service() -> AnalysisService:
        return AnalysisService(cached_dataset(settings.data_dir), settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if getattr(app.state, "service", None) is None:
            app.state.service = build_service()
        yield

    app = FastAPI(
        title="Windcast API",
        version="1.0.0",
        description="Decision-time wind forecasts and forecast accuracy for GB day-ahead purchasing.",
        lifespan=lifespan,
    )
    app.state.service = None
    app.state.service_factory = build_service
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET"], allow_headers=["*"]
    )
    install_request_logging(app)
    register_error_handlers(app)
    app.include_router(router)
    return app


app = create_app()
