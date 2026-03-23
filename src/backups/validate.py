"""
Path validation for backup procedures.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _is_remote_path(path: str) -> bool:
    """Check if path looks like a remote restic repo (s3:, rclone:, etc.)."""
    if ":" not in path:
        return False
    # Windows drive (e.g. C:\...) has ":" at position 1
    if len(path) >= 2 and path[1] == ":":
        return False
    return True


def validate_masterchief_config() -> tuple[list[str], str]:
    """
    Load and validate MASTERCHIEF_SRC and MASTERCHIEF_DEST from env.

    Returns:
        (source_paths, dest_path)

    Raises:
        ValueError: If env vars are missing, empty, or paths are invalid.
    """
    src_raw = os.getenv("MASTERCHIEF_SRC", "").strip()
    dest_raw = os.getenv("MASTERCHIEF_DEST", "").strip()

    if not src_raw:
        raise ValueError("MASTERCHIEF_SRC is not set or empty in .env")
    if not dest_raw:
        raise ValueError("MASTERCHIEF_DEST is not set or empty in .env")

    source_paths = [p.strip() for p in src_raw.split(",") if p.strip()]
    if not source_paths:
        raise ValueError("MASTERCHIEF_SRC contains no valid paths")

    # Validate each source path exists
    for p in source_paths:
        path = Path(p)
        if not path.exists():
            raise ValueError(f"Source path does not exist: {p}")

    # Validate dest: for local paths, parent dir must exist
    if not _is_remote_path(dest_raw):
        dest_path = Path(dest_raw)
        parent = dest_path.parent
        if parent != dest_path and not parent.exists():
            raise ValueError(f"Destination parent directory does not exist: {parent}")

    return source_paths, dest_raw
