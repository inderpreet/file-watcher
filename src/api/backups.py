"""
Backups API router.
"""

import json
import os

from fastapi import APIRouter, Request, HTTPException

from src.api import limiter
from src.backups.validate import validate_masterchief_config
from src.logger import logger
from src.restic.restic import backup_with_output
from src.storage.db import TABLE_RESTIC_LOGS, create, read_all

router = APIRouter(prefix="/backups", tags=["backups"])


@router.get("")
@limiter.limit("60/minute")
async def list_backups(request: Request):
    """List available backup endpoints."""
    return {"backups": ["masterchief"], "message": "Use POST /backups/masterchief/run to run MASTERCHIEF backup"}


@router.post("/masterchief/run")
@limiter.limit("10/minute")
async def run_masterchief_backup(request: Request):
    """
    Run MASTERCHIEF backup. SRC and DEST are read from .env (MASTERCHIEF_SRC, MASTERCHIEF_DEST).
    """
    try:
        source_paths, dest_path = validate_masterchief_config()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    password = os.getenv("MASTERCHIEF_PASSWORD", "").strip() or os.getenv("RESTIC_PASSWORD", "").strip() or None
    success, stdout, stderr, return_code = backup_with_output(
        repo_path=dest_path,
        sources=source_paths,
        password=password,
    )

    status = "success" if success else "failed"
    log_id = create(
        TABLE_RESTIC_LOGS,
        {
            "backup_name": "masterchief",
            "source_paths": json.dumps(source_paths),
            "dest_path": dest_path,
            "status": status,
            "stdout": stdout,
            "stderr": stderr,
            "return_code": return_code,
        },
    )

    response = {
        "status": status,
        "backup": "masterchief",
        "log_id": log_id,
        "stdout": stdout,
        "stderr": stderr,
        "message": "Backup completed" if success else f"Backup failed with return code {return_code}",
    }

    if not success:
        logger.error("MASTERCHIEF backup failed: {}", stderr)
        raise HTTPException(status_code=500, detail=response)

    return response


@router.get("/logs")
@limiter.limit("60/minute")
async def get_backup_logs(request: Request, limit: int = 20):
    """List recent RESTIC backup log entries."""
    rows = read_all(
        TABLE_RESTIC_LOGS,
        order_by="id DESC",
    )
    # Apply limit in Python (read_all doesn't support LIMIT)
    rows = rows[:limit]
    # Convert sqlite3.Row to dict for JSON
    logs = []
    for row in rows:
        d = dict(row)
        # Parse source_paths if needed for display
        if "source_paths" in d and isinstance(d["source_paths"], str):
            try:
                d["source_paths"] = json.loads(d["source_paths"])
            except json.JSONDecodeError:
                pass
        logs.append(d)
    return {"logs": logs}
