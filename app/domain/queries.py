"""Query parameters and a page of results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Generic, TypeVar

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 60
MAX_PAGE_SIZE = 120


class SortKey(StrEnum):
    TITLE_ASC = "title_asc"
    YEAR_DESC = "year_desc"
    YEAR_ASC = "year_asc"
    RATING_DESC = "rating_desc"
    RATING_ASC = "rating_asc"
    CREATED_DESC = "created_desc"


@dataclass(slots=True)
class MovieQuery:
    search: str | None = None
    genres: list[str] = field(default_factory=list)
    sort: SortKey = SortKey.CREATED_DESC
    limit: int = DEFAULT_PAGE_SIZE
    offset: int = 0


@dataclass(slots=True)
class Page(Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total
