"""
Backups API router.
"""

from fastapi import APIRouter, Request

from src.api import limiter

router = APIRouter(prefix="/backups", tags=["backups"])


@router.get("")
@limiter.limit("60/minute")
async def list_backups(request: Request):
    """Placeholder - backup endpoints to be added."""
    return {"message": "Backup endpoints coming soon"}
