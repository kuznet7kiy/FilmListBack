"""Request and response schemas for movies."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.domain.models import (
    RATING_MAX,
    RATING_MIN,
    YEAR_MAX,
    YEAR_MIN,
    Genre,
    Movie,
)

COVER_URL_PREFIX = "/media/covers"


def cover_url(filename: str | None) -> str | None:
    return f"{COVER_URL_PREFIX}/{filename}" if filename else None


class MovieBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    year: int = Field(ge=YEAR_MIN, le=YEAR_MAX)
    genres: list[Genre] = Field(min_length=1)
    rating: float = Field(ge=RATING_MIN, le=RATING_MAX)
    director: str = Field(default="", max_length=200)
    description: str = Field(default="", max_length=5000)
    cover_filename: str | None = None

    @field_validator("genres")
    @classmethod
    def _unique_genres(cls, value: list[str]) -> list[str]:
        seen: list[str] = []
        for genre in value:
            if genre not in seen:
                seen.append(genre)
        return seen

    @field_validator("title", "director", "description")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class MovieCreate(MovieBase):
    pass


class MovieUpdate(BaseModel):
    """Partial update: every field may be omitted."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    year: int | None = Field(default=None, ge=YEAR_MIN, le=YEAR_MAX)
    genres: list[Genre] | None = Field(default=None, min_length=1)
    rating: float | None = Field(default=None, ge=RATING_MIN, le=RATING_MAX)
    director: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    cover_filename: str | None = None

    model_config = {"extra": "forbid"}


class MovieOut(BaseModel):
    id: str
    title: str
    year: int
    genres: list[str]
    rating: float
    director: str
    description: str
    cover_filename: str | None
    cover_url: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_movie(cls, movie: Movie) -> MovieOut:
        return cls(
            id=movie.id,
            title=movie.title,
            year=movie.year,
            genres=movie.genres,
            rating=movie.rating,
            director=movie.director,
            description=movie.description,
            cover_filename=movie.cover_filename,
            cover_url=cover_url(movie.cover_filename),
            created_at=movie.created_at,
            updated_at=movie.updated_at,
        )


class MoviePageOut(BaseModel):
    items: list[MovieOut]
    total: int
    limit: int
    offset: int
    has_more: bool


class GenresOut(BaseModel):
    genres: list[str]
    counts: dict[str, int]
