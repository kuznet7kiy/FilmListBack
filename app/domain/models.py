"""The movie domain model and the fixed set of genres."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# The single source of truth for genres
GENRES: tuple[str, ...] = (
    "drama",
    "comedy",
    "action",
    "horror",
    "sci-fi",
    "thriller",
    "romance",
    "mystery",
)

Genre = Literal[
    "drama",
    "comedy",
    "action",
    "horror",
    "sci-fi",
    "thriller",
    "romance",
    "mystery",
]

YEAR_MIN = 1888
YEAR_MAX = 2035
RATING_MIN = 0.0
RATING_MAX = 10.0


class Movie(BaseModel):
    """A movie exactly as it is stored in the backend.

    ``title_norm`` is a denormalized field used for search and alphabetical
    ordering. It is stored alongside the data so that the JSON and Mongo
    implementations return the same order and the same search results.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str = Field(min_length=1, max_length=200)
    title_norm: str = ""
    year: int = Field(ge=YEAR_MIN, le=YEAR_MAX)
    genres: list[str] = Field(min_length=1)
    rating: float = Field(ge=RATING_MIN, le=RATING_MAX)
    director: str = Field(default="", max_length=200)
    description: str = Field(default="", max_length=5000)
    cover_filename: str | None = None
    created_at: datetime
    updated_at: datetime
