"""
Restic API router.
"""

import os
from fastapi import APIRouter, Request, HTTPException

from src.api import limiter
from src.logger import logger
from src.restic.restic import list_snapshots, ResticError

router = APIRouter(prefix="/restic", tags=["restic"])


@router.get("/snapshots")
@limiter.limit("60/minute")
async def get_snapshots(request: Request, repo: str | None = None):
    """List snapshots in the restic repository."""
    repo_path = repo or os.getenv("RESTIC_REPOSITORY", "").strip()
    if not repo_path:
        raise HTTPException(
            status_code=400,
            detail="Repository path required. Set RESTIC_REPOSITORY in .env or pass ?repo=...",
        )
    try:
        output = list_snapshots(repo_path)
        return {"snapshots": output}
    except ResticError as e:
        logger.error("Restic error: {}", str(e))
        raise HTTPException(status_code=500, detail=str(e))
