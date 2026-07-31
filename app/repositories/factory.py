"""Storage implementation selection.

The only place in the project that knows about the concrete implementations.
The Mongo driver is imported lazily, inside the branch, so without
``MONGODB_URI`` the app starts up even when pymongo is not installed.
"""

from __future__ import annotations

import logging

from app.config import Settings
from app.repositories.base import MovieRepository

logger = logging.getLogger(__name__)


def build_repository(settings: Settings) -> MovieRepository:
    if settings.use_mongo:
        try:
            from app.repositories.mongo import MongoMovieRepository
        except ImportError as exc:
            raise RuntimeError(
                "MONGODB_URI is set, but the MongoDB driver is not installed. "
                "Run: pip install -r requirements-mongo.txt"
            ) from exc

        logger.info("Storage: MongoDB, database %s", settings.mongodb_db)
        return MongoMovieRepository(
            settings.mongodb_uri,
            settings.mongodb_db,
            settings.mongodb_collection,
        )

    from app.repositories.json_file import JsonFileMovieRepository

    logger.info("Storage: JSON file %s (MONGODB_URI is not set)", settings.movies_file)
    return JsonFileMovieRepository(settings.movies_file)
