"""
API module - FastAPI routers for restic, storage, backups.
"""

from fastapi import APIRouter
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

from . import restic, storage, backups

api = APIRouter(prefix="/api/v1")
api.include_router(restic.router)
api.include_router(storage.router)
api.include_router(backups.router)
