from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import MovieServiceDep
from app.schemas.stats import StatsOut

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsOut)
async def library_stats(service: MovieServiceDep) -> StatsOut:
    return StatsOut.from_stats(await service.stats())
