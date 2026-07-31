from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import RepositoryDep
from app.schemas.common import HealthOut

router = APIRouter(tags=["service"])


@router.get("/health", response_model=HealthOut)
async def health(repo: RepositoryDep) -> HealthOut:
    """Reports which storage backend is connected: json or mongo."""
    return HealthOut(status="ok", backend=repo.backend_name)
