"""The storage contract.

Everything above this file knows only about ``MovieRepository``. Neither the
routes nor the services have any idea whether the data lives in a JSON file or
in MongoDB — which is why switching to Mongo comes down to one environment
variable.
"""

from __future__ import annotations

import abc
from typing import Any

from app.domain.models import Movie
from app.domain.queries import MovieQuery, Page
from app.domain.stats import LibraryStats


class MovieRepository(abc.ABC):
    #json | mongo 
    backend_name: str = "unknown"

    @abc.abstractmethod
    async def init(self) -> None:
        """Open the connection / load the file / create indexes."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Release resources."""

    @abc.abstractmethod
    async def create(self, movie: Movie) -> Movie: ...

    @abc.abstractmethod
    async def get(self, movie_id: str) -> Movie | None: ...

    @abc.abstractmethod
    async def update(self, movie_id: str, patch: dict[str, Any]) -> Movie | None:
        """Partial update. ``None`` means there is no such movie."""

    @abc.abstractmethod
    async def delete(self, movie_id: str) -> bool:
        """``False`` means there was nothing to delete."""

    @abc.abstractmethod
    async def list(self, query: MovieQuery) -> Page[Movie]: ...

    @abc.abstractmethod
    async def stats(self) -> LibraryStats: ...

    @abc.abstractmethod
    async def genre_counts(self) -> dict[str, int]:
        """How many movies each genre has — for the counts next to the checkboxes."""
