from __future__ import annotations


class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class MovieNotFound(DomainError):
    code = "movie_not_found"

    def __init__(self, movie_id: str) -> None:
        super().__init__(f"Movie {movie_id} not found")
        self.movie_id = movie_id


class InvalidUpload(DomainError):
    code = "invalid_upload"


class RepositoryError(DomainError):
    code = "repository_error"
