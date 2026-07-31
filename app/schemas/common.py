"""Shared schemas."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorOut(BaseModel):
    detail: str
    code: str


class HealthOut(BaseModel):
    status: str
    backend: str


class CoverUploadOut(BaseModel):
    filename: str
    url: str
    size: int
    content_type: str
