"""Dashboard response schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.domain.stats import LibraryStats
from app.schemas.movie import cover_url


class GenreCountOut(BaseModel):
    genre: str
    count: int


class DecadeCountOut(BaseModel):
    decade: int
    count: int


class DirectorCountOut(BaseModel):
    director: str
    count: int


class TopRatedOut(BaseModel):
    id: str
    title: str
    year: int
    rating: float
    cover_url: str | None


class StatsOut(BaseModel):
    total: int
    avg_rating: float
    by_genre: list[GenreCountOut]
    by_decade: list[DecadeCountOut]
    top_rated: list[TopRatedOut]
    top_directors: list[DirectorCountOut]
    directors_count: int
    year_min: int | None
    year_max: int | None
    added_last_30_days: int

    @classmethod
    def from_stats(cls, stats: LibraryStats) -> StatsOut:
        return cls(
            total=stats.total,
            avg_rating=stats.avg_rating,
            by_genre=[GenreCountOut(genre=g.genre, count=g.count) for g in stats.by_genre],
            by_decade=[DecadeCountOut(decade=d.decade, count=d.count) for d in stats.by_decade],
            top_rated=[
                TopRatedOut(
                    id=m.id,
                    title=m.title,
                    year=m.year,
                    rating=m.rating,
                    cover_url=cover_url(m.cover_filename),
                )
                for m in stats.top_rated
            ],
            top_directors=[
                DirectorCountOut(director=d.director, count=d.count) for d in stats.top_directors
            ],
            directors_count=stats.directors_count,
            year_min=stats.year_min,
            year_max=stats.year_max,
            added_last_30_days=stats.added_last_30_days,
        )
