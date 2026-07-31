from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions import DomainError, InvalidUpload, MovieNotFound, RepositoryError

logger = logging.getLogger(__name__)

_STATUS_BY_ERROR: tuple[tuple[type[DomainError], int], ...] = (
    (MovieNotFound, status.HTTP_404_NOT_FOUND),
    (InvalidUpload, status.HTTP_400_BAD_REQUEST),
    (RepositoryError, status.HTTP_503_SERVICE_UNAVAILABLE),
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        code = status.HTTP_500_INTERNAL_SERVER_ERROR
        for error_type, http_status in _STATUS_BY_ERROR:
            if isinstance(exc, error_type):
                code = http_status
                break
        if code >= 500:
            logger.exception("Unhandled domain error", exc_info=exc)
        return JSONResponse(status_code=code, content={"detail": exc.message, "code": exc.code})
