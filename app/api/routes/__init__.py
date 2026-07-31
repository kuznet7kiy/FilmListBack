"""Assembles every router under the shared /api prefix."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import genres, health, movies, stats, uploads

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(genres.router)
api_router.include_router(movies.router)
api_router.include_router(uploads.router)
api_router.include_router(stats.router)
