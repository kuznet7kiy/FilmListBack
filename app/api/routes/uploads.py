from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Response, UploadFile, status

from app.api.deps import StorageDep
from app.schemas.common import CoverUploadOut
from app.schemas.movie import cover_url

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/cover", response_model=CoverUploadOut, status_code=status.HTTP_201_CREATED)
async def upload_cover(
    storage: StorageDep,
    file: Annotated[UploadFile, File(description="Cover image")],
) -> CoverUploadOut:
    """Upload a cover as a separate step.

    The returned ``filename`` is then sent in the body when creating or editing
    a movie. This keeps every other endpoint pure JSON, and lets the form show a
    preview before anything is saved.
    """
    filename, size, content_type = await storage.save(file)
    return CoverUploadOut(
        filename=filename,
        url=cover_url(filename) or "",
        size=size,
        content_type=content_type,
    )


@router.delete("/cover/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cover(filename: str, storage: StorageDep) -> Response:
    """Clean up a cover uploaded into a form that was ultimately cancelled."""
    await storage.delete(filename)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
