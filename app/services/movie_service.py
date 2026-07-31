"""Application logic for movies.

This is where all the rules that do not depend on where the data lives belong:
id generation, title normalization, timestamps and cover-file cleanup.
"""

from __future__ import annotations

from typing import Any

from app.domain.exceptions import MovieNotFound
from app.domain.models import Movie
from app.domain.queries import MovieQuery, Page
from app.domain.stats import LibraryStats
from app.repositories.base import MovieRepository
from app.schemas.movie import MovieCreate, MovieUpdate
from app.services.storage import CoverStorage
from app.utils.ids import new_id
from app.utils.text import normalize_title
from app.utils.timeutils import utcnow


class MovieService:
    def __init__(self, repo: MovieRepository, storage: CoverStorage) -> None:
        self._repo = repo
        self._storage = storage

    async def list(self, query: MovieQuery) -> Page[Movie]:
        if query.search:
            query.search = normalize_title(query.search)
        return await self._repo.list(query)

    async def get(self, movie_id: str) -> Movie:
        movie = await self._repo.get(movie_id)
        if movie is None:
            raise MovieNotFound(movie_id)
        return movie

    async def create(self, payload: MovieCreate) -> Movie:
        now = utcnow()
        movie = Movie(
            id=new_id(),
            title=payload.title,
            title_norm=normalize_title(payload.title),
            year=payload.year,
            genres=list(payload.genres),
            rating=payload.rating,
            director=payload.director,
            description=payload.description,
            cover_filename=payload.cover_filename,
            created_at=now,
            updated_at=now,
        )
        return await self._repo.create(movie)

    async def update(self, movie_id: str, payload: MovieUpdate) -> Movie:
        current = await self.get(movie_id)

        patch: dict[str, Any] = payload.model_dump(exclude_unset=True)
        if "title" in patch:
            patch["title"] = patch["title"].strip()
            patch["title_norm"] = normalize_title(patch["title"])
        if "genres" in patch:
            patch["genres"] = list(dict.fromkeys(patch["genres"]))

        old_cover = current.cover_filename
        cover_replaced = "cover_filename" in patch and patch["cover_filename"] != old_cover

        patch["updated_at"] = utcnow()
        updated = await self._repo.update(movie_id, patch)
        if updated is None:
            raise MovieNotFound(movie_id)

        if cover_replaced:
            await self._storage.delete(old_cover)
        return updated

    async def delete(self, movie_id: str) -> None:
        movie = await self.get(movie_id)
        deleted = await self._repo.delete(movie_id)
        if not deleted:
            raise MovieNotFound(movie_id)
        await self._storage.delete(movie.cover_filename)

    async def genre_counts(self) -> dict[str, int]:
        return await self._repo.genre_counts()

    async def stats(self) -> LibraryStats:
        return await self._repo.stats()
