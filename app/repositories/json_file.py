"""Storage implementation backed by a JSON file.

Runs without any external services — this is the default mode until
``MONGODB_URI`` is set. The whole dataset is kept in memory and flushed to disk
atomically (write to a temp file + ``os.replace``), so a crash mid-write cannot
leave a truncated JSON file behind.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections import Counter
from datetime import timedelta
from operator import attrgetter
from pathlib import Path
from typing import Any

import aiofiles

from app.domain.models import Movie
from app.domain.queries import MovieQuery, Page
from app.domain.stats import (
    DecadeCount,
    DirectorCount,
    GenreCount,
    LibraryStats,
    TopRatedMovie,
)
from app.repositories._sorting import SORT_SPEC, TIEBREAKER
from app.repositories.base import MovieRepository
from app.utils.timeutils import utcnow

_OFFLOAD_THRESHOLD = 500


class JsonFileMovieRepository(MovieRepository):
    backend_name = "json"

    def __init__(self, path: Path) -> None:
        self._path = path
        self._items: dict[str, Movie] = {}
        self._lock = asyncio.Lock()

    async def init(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._items = {}
            return

        async with aiofiles.open(self._path, "r", encoding="utf-8") as fh:
            raw = await fh.read()

        payload = json.loads(raw) if raw.strip() else []
        self._items = {item["id"]: Movie.model_validate(item) for item in payload}

    async def close(self) -> None:
        return None

    #write

    async def create(self, movie: Movie) -> Movie:
        async with self._lock:
            self._items[movie.id] = movie
            await self._persist()
        return movie

    async def update(self, movie_id: str, patch: dict[str, Any]) -> Movie | None:
        async with self._lock:
            current = self._items.get(movie_id)
            if current is None:
                return None
            updated = current.model_copy(update=patch)
            self._items[movie_id] = updated
            await self._persist()
        return updated

    async def delete(self, movie_id: str) -> bool:
        async with self._lock:
            if self._items.pop(movie_id, None) is None:
                return False
            await self._persist()
        return True

    async def _persist(self) -> None:
        """Atomically rewrite the whole file. Called while holding ``self._lock``."""
        items = [movie.model_dump(mode="json") for movie in self._items.values()]

        def dump() -> str:
            return json.dumps(items, ensure_ascii=False, indent=2)

        if len(items) > _OFFLOAD_THRESHOLD:
            raw = await asyncio.to_thread(dump)
        else:
            raw = dump()

        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        async with aiofiles.open(tmp_path, "w", encoding="utf-8") as fh:
            await fh.write(raw)
        await asyncio.to_thread(os.replace, tmp_path, self._path)

    #read

    async def get(self, movie_id: str) -> Movie | None:
        return self._items.get(movie_id)

    async def list(self, query: MovieQuery) -> Page[Movie]:
        items = self._filter(query)
        self._sort(items, query)
        window = items[query.offset : query.offset + query.limit]
        return Page(items=window, total=len(items), limit=query.limit, offset=query.offset)

    def _filter(self, query: MovieQuery) -> list[Movie]:
        items = list(self._items.values())

        if query.search:
            needle = query.search
            items = [m for m in items if needle in m.title_norm]

        if query.genres:
            wanted = set(query.genres)
            items = [m for m in items if wanted & set(m.genres)]

        return items

    @staticmethod
    def _sort(items: list[Movie], query: MovieQuery) -> None:
        field, descending = SORT_SPEC[query.sort]

        items.sort(key=attrgetter(TIEBREAKER))
        if field != TIEBREAKER:
            items.sort(key=attrgetter(field), reverse=descending)
        elif descending:
            items.reverse()

    async def genre_counts(self) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for movie in self._items.values():
            counter.update(movie.genres)
        return dict(counter)

    async def stats(self) -> LibraryStats:
        movies = list(self._items.values())
        if not movies:
            return LibraryStats()

        ratings = [m.rating for m in movies]
        years = [m.year for m in movies]
        directors = [m.director.strip() for m in movies if m.director.strip()]

        genre_counter: Counter[str] = Counter()
        decade_counter: Counter[int] = Counter()
        for movie in movies:
            genre_counter.update(movie.genres)
            decade_counter[movie.year // 10 * 10] += 1

        director_counter = Counter(directors)
        cutoff = utcnow() - timedelta(days=30)
        top_rated = sorted(movies, key=lambda m: (-m.rating, m.title_norm))[:5]

        return LibraryStats(
            total=len(movies),
            avg_rating=round(sum(ratings) / len(ratings), 2),
            by_genre=[
                GenreCount(genre=genre, count=count)
                for genre, count in genre_counter.most_common()
            ],
            by_decade=[
                DecadeCount(decade=decade, count=decade_counter[decade])
                for decade in sorted(decade_counter)
            ],
            top_rated=[
                TopRatedMovie(
                    id=m.id,
                    title=m.title,
                    year=m.year,
                    rating=m.rating,
                    cover_filename=m.cover_filename,
                )
                for m in top_rated
            ],
            top_directors=[
                DirectorCount(director=name, count=count)
                for name, count in director_counter.most_common(5)
            ],
            directors_count=len(director_counter),
            year_min=min(years),
            year_max=max(years),
            added_last_30_days=sum(1 for m in movies if m.created_at >= cutoff),
        )
