"""
Storage API router - file details CRUD.
"""

from fastapi import APIRouter, Request, HTTPException, Query

from pydantic import BaseModel, Field

from src.api import limiter
from src.storage.db import (
    get_connection,
    create,
    read,
    read_all,
    read_by_ids,
    update,
    delete,
    bulk_create,
    bulk_delete,
    TABLE_FILE_DETAILS,
)

router = APIRouter(prefix="/storage", tags=["storage"])


# --- Schemas ---


class FileRecordCreate(BaseModel):
    file_name: str = Field(..., min_length=1)
    size: int = Field(..., ge=0)
    hash: str = Field(..., min_length=1)
    complete_path: str = Field(..., min_length=1)
    file_created_at: str | None = None
    file_modified_at: str | None = None


class FileRecordUpdate(BaseModel):
    file_name: str | None = None
    size: int | None = Field(None, ge=0)
    hash: str | None = None
    complete_path: str | None = None
    file_created_at: str | None = None
    file_modified_at: str | None = None


class FileRecordResponse(BaseModel):
    id: int
    file_name: str
    size: int
    hash: str
    complete_path: str
    file_created_at: str | None = None
    file_modified_at: str | None = None
    created_at: str | None = None


class BulkCreateRequest(BaseModel):
    files: list[FileRecordCreate]


class BulkDeleteRequest(BaseModel):
    ids: list[int]


class BulkIdsRequest(BaseModel):
    ids: list[int]


def _row_to_dict(row) -> dict:
    return dict(row) if row else None


# --- Health ---


@router.get("/health")
@limiter.limit("60/minute")
async def storage_health(request: Request):
    """Check database connectivity."""
    try:
        conn = get_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# --- Single file CRUD ---


@router.post("/files", response_model=dict)
@limiter.limit("60/minute")
async def create_file_record(request: Request, body: FileRecordCreate):
    """Create a single file record."""
    try:
        data = body.model_dump()
        row_id = create(TABLE_FILE_DETAILS, data)
        row = read(TABLE_FILE_DETAILS, id_value=row_id)
        return _row_to_dict(row)
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(400, f"File already exists: {body.complete_path}")
        raise HTTPException(500, str(e))


@router.get("/files/{file_id}", response_model=dict)
@limiter.limit("60/minute")
async def get_file_record(request: Request, file_id: int):
    """Get a single file record by ID."""
    row = read(TABLE_FILE_DETAILS, id_value=file_id)
    if not row:
        raise HTTPException(404, "File record not found")
    return _row_to_dict(row)


@router.get("/files", response_model=list)
@limiter.limit("60/minute")
async def list_file_records(
    request: Request,
    path: str | None = Query(None, description="Filter by complete_path contains"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List file records with optional filter and pagination."""
    if path:
        rows = read_all(
            TABLE_FILE_DETAILS,
            where="complete_path LIKE ?",
            params=(f"%{path}%",),
            order_by="id ASC",
        )
    else:
        rows = read_all(TABLE_FILE_DETAILS, order_by="id ASC")
    # Apply limit/offset
    rows = rows[offset : offset + limit]
    return [_row_to_dict(r) for r in rows]


@router.put("/files/{file_id}", response_model=dict)
@limiter.limit("60/minute")
async def update_file_record(request: Request, file_id: int, body: FileRecordUpdate):
    """Update a single file record."""
    row = read(TABLE_FILE_DETAILS, id_value=file_id)
    if not row:
        raise HTTPException(404, "File record not found")
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        return _row_to_dict(row)
    update(TABLE_FILE_DETAILS, "id", file_id, data)
    row = read(TABLE_FILE_DETAILS, id_value=file_id)
    return _row_to_dict(row)


@router.delete("/files/{file_id}")
@limiter.limit("60/minute")
async def delete_file_record(request: Request, file_id: int):
    """Delete a single file record."""
    count = delete(TABLE_FILE_DETAILS, "id", file_id)
    if count == 0:
        raise HTTPException(404, "File record not found")
    return {"deleted": file_id, "count": count}


# --- Bulk operations ---


@router.post("/files/bulk", response_model=dict)
@limiter.limit("60/minute")
async def bulk_create_file_records(request: Request, body: BulkCreateRequest):
    """Create multiple file records."""
    if not body.files:
        return {"created": 0, "ids": []}
    rows = [f.model_dump() for f in body.files]
    try:
        ids = bulk_create(TABLE_FILE_DETAILS, rows)
        return {"created": len(ids), "ids": ids}
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(400, "One or more files already exist (duplicate complete_path)")
        raise HTTPException(500, str(e))


@router.post("/files/bulk/get", response_model=list)
@limiter.limit("60/minute")
async def bulk_get_file_records(request: Request, body: BulkIdsRequest):
    """Get multiple file records by IDs."""
    if not body.ids:
        return []
    rows = read_by_ids(TABLE_FILE_DETAILS, "id", body.ids)
    return [_row_to_dict(r) for r in rows]


@router.delete("/files/bulk", response_model=dict)
@limiter.limit("60/minute")
async def bulk_delete_file_records(request: Request, body: BulkDeleteRequest):
    """Delete multiple file records by IDs."""
    if not body.ids:
        return {"deleted": 0}
    count = bulk_delete(TABLE_FILE_DETAILS, "id", body.ids)
    return {"deleted": count, "ids": body.ids}
