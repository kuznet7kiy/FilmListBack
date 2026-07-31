from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import MovieServiceDep
from app.domain.models import GENRES
from app.schemas.movie import GenresOut

router = APIRouter(tags=["genres"])


@router.get("/genres", response_model=GenresOut)
async def list_genres(service: MovieServiceDep) -> GenresOut:
    """The fixed set of genres plus counts for the filter checkboxes."""
    counts = await service.genre_counts()
    return GenresOut(genres=list(GENRES), counts={g: counts.get(g, 0) for g in GENRES})
