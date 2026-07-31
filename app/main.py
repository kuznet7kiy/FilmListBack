"""Application entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.errors import register_error_handlers
from app.api.routes import api_router
from app.config import Settings, get_settings
from app.repositories.factory import build_repository
from app.services.storage import CoverStorage

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.covers_dir.mkdir(parents=True, exist_ok=True)

    repository = build_repository(settings)
    try:
        await repository.init()
    except Exception:
        logger.error(
            "Could not connect to the %r storage backend. "
            "Check MONGODB_URI in backend/.env, or clear it "
            "to run on the JSON file.",
            repository.backend_name,
        )
        raise

    app.state.repository = repository
    app.state.storage = CoverStorage(settings.covers_dir, settings.max_upload_bytes)
    logger.info("Storage ready: %s", repository.backend_name)

    try:
        yield
    finally:
        await repository.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Movie Library API",
        description="A library of movies you have watched",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    settings.covers_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")
    app.include_router(api_router)
    register_error_handlers(app)
    return app


app = create_app()
