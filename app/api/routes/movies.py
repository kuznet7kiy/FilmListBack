from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import MovieServiceDep
from app.domain.models import Genre
from app.domain.queries import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MovieQuery, SortKey
from app.schemas.movie import MovieCreate, MovieOut, MoviePageOut, MovieUpdate

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=MoviePageOut)
async def list_movies(
    service: MovieServiceDep,
    search: Annotated[str | None, Query(max_length=200, description="Search by title")] = None,
    genres: Annotated[
        list[Genre] | None,
        Query(description="Genres; a movie matches if at least one of them matches"),
    ] = None,
    sort: Annotated[SortKey, Query()] = SortKey.CREATED_DESC,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MoviePageOut:
    page = await service.list(
        MovieQuery(
            search=search or None,
            genres=list(genres or []),
            sort=sort,
            limit=limit,
            offset=offset,
        )
    )
    return MoviePageOut(
        items=[MovieOut.from_movie(m) for m in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
        has_more=page.has_more,
    )


@router.post("", response_model=MovieOut, status_code=status.HTTP_201_CREATED)
async def create_movie(payload: MovieCreate, service: MovieServiceDep) -> MovieOut:
    return MovieOut.from_movie(await service.create(payload))


@router.get("/{movie_id}", response_model=MovieOut)
async def get_movie(movie_id: str, service: MovieServiceDep) -> MovieOut:
    return MovieOut.from_movie(await service.get(movie_id))


@router.patch("/{movie_id}", response_model=MovieOut)
async def update_movie(
    movie_id: str, payload: MovieUpdate, service: MovieServiceDep
) -> MovieOut:
    return MovieOut.from_movie(await service.update(movie_id, payload))


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: str, service: MovieServiceDep) -> Response:
    await service.delete(movie_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
