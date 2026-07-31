from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.repositories.base import MovieRepository
from app.services.movie_service import MovieService
from app.services.storage import CoverStorage


def get_repository(request: Request) -> MovieRepository:
    return request.app.state.repository


def get_storage(request: Request) -> CoverStorage:
    return request.app.state.storage


def get_movie_service(
    repo: Annotated[MovieRepository, Depends(get_repository)],
    storage: Annotated[CoverStorage, Depends(get_storage)],
) -> MovieService:
    return MovieService(repo, storage)


RepositoryDep = Annotated[MovieRepository, Depends(get_repository)]
StorageDep = Annotated[CoverStorage, Depends(get_storage)]
MovieServiceDep = Annotated[MovieService, Depends(get_movie_service)]
