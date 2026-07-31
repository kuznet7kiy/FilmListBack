"""Storage implementation backed by MongoDB.

Imported only from ``factory.py``, and only when ``MONGODB_URI`` is set, so the
driver does not even have to be installed when Mongo is not in use.

Uses PyMongo's built-in async client (``AsyncMongoClient``, available since
4.13) — motor is no longer needed, it was only a wrapper around the same thing.
"""

from __future__ import annotations

import re
from datetime import timedelta
from typing import Any

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient, ReturnDocument

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


def _to_doc(movie: Movie) -> dict[str, Any]:
    doc = movie.model_dump()
    doc["_id"] = doc.pop("id")
    return doc


def _to_movie(doc: dict[str, Any]) -> Movie:
    data = dict(doc)
    data["id"] = data.pop("_id")
    return Movie.model_validate(data)


class MongoMovieRepository(MovieRepository):
    backend_name = "mongo"

    def __init__(self, uri: str, db_name: str, collection_name: str) -> None:
        self._client: AsyncMongoClient = AsyncMongoClient(uri, tz_aware=True)
        self._collection = self._client[db_name][collection_name]

    async def init(self) -> None:
        await self._client.admin.command("ping")
        await self._collection.create_index([("title_norm", ASCENDING)])
        await self._collection.create_index([("genres", ASCENDING)])
        await self._collection.create_index([("year", DESCENDING)])
        await self._collection.create_index([("rating", DESCENDING)])
        await self._collection.create_index([("created_at", DESCENDING)])

    async def close(self) -> None:
        await self._client.close()

    #write
    async def create(self, movie: Movie) -> Movie:
        await self._collection.insert_one(_to_doc(movie))
        return movie

    async def update(self, movie_id: str, patch: dict[str, Any]) -> Movie | None:
        doc = await self._collection.find_one_and_update(
            {"_id": movie_id},
            {"$set": patch},
            return_document=ReturnDocument.AFTER,
        )
        return _to_movie(doc) if doc else None

    async def delete(self, movie_id: str) -> bool:
        result = await self._collection.delete_one({"_id": movie_id})
        return result.deleted_count > 0

    #read

    async def get(self, movie_id: str) -> Movie | None:
        doc = await self._collection.find_one({"_id": movie_id})
        return _to_movie(doc) if doc else None

    async def list(self, query: MovieQuery) -> Page[Movie]:
        criteria = self._criteria(query)
        field, descending = SORT_SPEC[query.sort]
        sort_spec = [(field, DESCENDING if descending else ASCENDING)]
        if field != TIEBREAKER:
            sort_spec.append((TIEBREAKER, ASCENDING))

        cursor = (
            self._collection.find(criteria)
            .sort(sort_spec)
            .skip(query.offset)
            .limit(query.limit)
        )
        docs = await cursor.to_list(length=query.limit)
        total = await self._collection.count_documents(criteria)

        return Page(
            items=[_to_movie(doc) for doc in docs],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    @staticmethod
    def _criteria(query: MovieQuery) -> dict[str, Any]:
        criteria: dict[str, Any] = {}
        if query.search:
            # title_norm - lowercased
            criteria["title_norm"] = {"$regex": re.escape(query.search)}
        if query.genres:
            criteria["genres"] = {"$in": query.genres}
        return criteria

    async def genre_counts(self) -> dict[str, int]:
        pipeline = [
            {"$unwind": "$genres"},
            {"$group": {"_id": "$genres", "count": {"$sum": 1}}},
        ]
        rows = await self._collection.aggregate(pipeline).to_list(length=None)
        return {row["_id"]: row["count"] for row in rows}

    async def stats(self) -> LibraryStats:
        cutoff = utcnow() - timedelta(days=30)
        pipeline = [
            {
                "$facet": {
                    "totals": [
                        {
                            "$group": {
                                "_id": None,
                                "total": {"$sum": 1},
                                "avg_rating": {"$avg": "$rating"},
                                "year_min": {"$min": "$year"},
                                "year_max": {"$max": "$year"},
                            }
                        }
                    ],
                    "by_genre": [
                        {"$unwind": "$genres"},
                        {"$group": {"_id": "$genres", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1, "_id": 1}},
                    ],
                    "by_decade": [
                        {
                            "$group": {
                                "_id": {"$subtract": ["$year", {"$mod": ["$year", 10]}]},
                                "count": {"$sum": 1},
                            }
                        },
                        {"$sort": {"_id": 1}},
                    ],
                    "top_rated": [
                        {"$sort": {"rating": -1, "title_norm": 1}},
                        {"$limit": 5},
                        {
                            "$project": {
                                "title": 1,
                                "year": 1,
                                "rating": 1,
                                "cover_filename": 1,
                            }
                        },
                    ],
                    "directors": [
                        {"$match": {"director": {"$nin": ["", None]}}},
                        {"$group": {"_id": "$director", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1, "_id": 1}},
                    ],
                    "recent": [
                        {"$match": {"created_at": {"$gte": cutoff}}},
                        {"$count": "count"},
                    ],
                }
            }
        ]
        result = await self._collection.aggregate(pipeline).to_list(length=1)
        if not result:
            return LibraryStats()

        facet = result[0]
        totals = facet["totals"][0] if facet["totals"] else {}
        if not totals.get("total"):
            return LibraryStats()

        directors = facet["directors"]
        recent = facet["recent"]

        return LibraryStats(
            total=totals["total"],
            avg_rating=round(totals.get("avg_rating") or 0.0, 2),
            by_genre=[
                GenreCount(genre=row["_id"], count=row["count"]) for row in facet["by_genre"]
            ],
            by_decade=[
                DecadeCount(decade=row["_id"], count=row["count"]) for row in facet["by_decade"]
            ],
            top_rated=[
                TopRatedMovie(
                    id=row["_id"],
                    title=row["title"],
                    year=row["year"],
                    rating=row["rating"],
                    cover_filename=row.get("cover_filename"),
                )
                for row in facet["top_rated"]
            ],
            top_directors=[
                DirectorCount(director=row["_id"], count=row["count"]) for row in directors[:5]
            ],
            directors_count=len(directors),
            year_min=totals.get("year_min"),
            year_max=totals.get("year_max"),
            added_last_30_days=recent[0]["count"] if recent else 0,
        )
