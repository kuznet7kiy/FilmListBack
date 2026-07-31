"""Aggregates for the dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class GenreCount:
    genre: str
    count: int


@dataclass(slots=True)
class DecadeCount:
    decade: int
    count: int


@dataclass(slots=True)
class DirectorCount:
    director: str
    count: int


@dataclass(slots=True)
class TopRatedMovie:
    id: str
    title: str
    year: int
    rating: float
    cover_filename: str | None


@dataclass(slots=True)
class LibraryStats:
    total: int = 0
    avg_rating: float = 0.0
    by_genre: list[GenreCount] = field(default_factory=list)
    by_decade: list[DecadeCount] = field(default_factory=list)
    top_rated: list[TopRatedMovie] = field(default_factory=list)
    top_directors: list[DirectorCount] = field(default_factory=list)
    directors_count: int = 0
    year_min: int | None = None
    year_max: int | None = None
    added_last_30_days: int = 0
