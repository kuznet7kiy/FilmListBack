from __future__ import annotations

import argparse
import asyncio
import random
import sys
from datetime import timedelta

import aiofiles

from app.config import get_settings
from app.domain.models import Movie
from app.domain.queries import MAX_PAGE_SIZE, MovieQuery
from app.repositories.base import MovieRepository
from app.repositories.factory import build_repository
from app.utils.ids import new_id
from app.utils.text import normalize_title
from app.utils.timeutils import utcnow
from scripts._covers import render_cover
from scripts._dataset import MOVIES


async def _clear(repo: MovieRepository) -> int:
    removed = 0
    while True:
        page = await repo.list(MovieQuery(limit=MAX_PAGE_SIZE))
        if not page.items:
            return removed
        for movie in page.items:
            await repo.delete(movie.id)
            removed += 1


async def seed(force: bool) -> int:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.covers_dir.mkdir(parents=True, exist_ok=True)

    repo = build_repository(settings)
    await repo.init()
    try:
        existing = await repo.list(MovieQuery(limit=1))
        if existing.total and not force:
            print(
                f"The library already holds {existing.total} movie(s). "
                "Run with --force to overwrite it."
            )
            return 1
        if existing.total:
            removed = await _clear(repo)
            print(f"Movies removed: {removed}")
        rng = random.Random(20240730)
        now = utcnow()

        for index, (title, year, genres, rating, director, description) in enumerate(MOVIES):
            cover_filename = f"{new_id()}.svg"
            async with aiofiles.open(settings.covers_dir / cover_filename, "wb") as fh:
                await fh.write(render_cover(title, year))

            created = now - timedelta(days=rng.randint(0, 120), minutes=index)
            await repo.create(
                Movie(
                    id=new_id(),
                    title=title,
                    title_norm=normalize_title(title),
                    year=year,
                    genres=list(genres),
                    rating=rating,
                    director=director,
                    description=description,
                    cover_filename=cover_filename,
                    created_at=created,
                    updated_at=created,
                )
            )

        print(f"Movies added: {len(MOVIES)} (storage: {repo.backend_name})")
        return 0
    finally:
        await repo.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill the library with demo movies")
    parser.add_argument("--force", action="store_true", help="clear the library before seeding")
    args = parser.parse_args()
    return asyncio.run(seed(args.force))


if __name__ == "__main__":
    sys.exit(main())
