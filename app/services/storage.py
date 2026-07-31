"""Cover storage on disk.

Files are streamed to disk chunk by chunk: a plain ``await file.read()`` is
dangerous — an image of any size ends up entirely in memory, and the size limit
would only be checked after the fact.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.domain.exceptions import InvalidUpload
from app.utils.ids import new_id

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024

_SIGNATURES: tuple[tuple[bytes, str, str], ...] = (
    (b"\xff\xd8\xff", ".jpg", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", ".png", "image/png"),
    (b"GIF8", ".gif", "image/gif"),
)

_FILENAME_RE = re.compile(r"^[0-9a-f]{32}\.(jpg|png|gif|webp|svg)$")


def _sniff(head: bytes) -> tuple[str, str]:
    for signature, extension, content_type in _SIGNATURES:
        if head.startswith(signature):
            return extension, content_type
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp", "image/webp"
    raise InvalidUpload("Only JPEG, PNG, WebP or GIF images are supported")


class CoverStorage:
    def __init__(self, covers_dir: Path, max_bytes: int) -> None:
        self._dir = covers_dir
        self._max_bytes = max_bytes
        self._dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, filename: str) -> Path:
        if not _FILENAME_RE.match(filename):
            raise InvalidUpload("Invalid cover filename")
        return self._dir / filename

    async def save(self, file: UploadFile) -> tuple[str, int, str]:
        """Save a cover and return (filename, size, MIME type)."""
        head = await file.read(CHUNK_SIZE)
        if not head:
            raise InvalidUpload("Empty file")

        extension, content_type = _sniff(head)
        filename = f"{new_id()}{extension}"
        target = self._dir / filename

        size = 0
        chunk = head
        try:
            async with aiofiles.open(target, "wb") as fh:
                while chunk:
                    size += len(chunk)
                    if size > self._max_bytes:
                        raise InvalidUpload(
                            f"File exceeds the {self._max_bytes // 1024 // 1024} MB limit"
                        )
                    await fh.write(chunk)
                    chunk = await file.read(CHUNK_SIZE)
        except Exception:
            target.unlink(missing_ok=True)
            raise

        return filename, size, content_type

    async def delete(self, filename: str | None) -> None:
        if not filename:
            return
        try:
            self.path_for(filename).unlink(missing_ok=True)
        except InvalidUpload:
            logger.warning("Skipped deleting a cover with an invalid name: %r", filename)
