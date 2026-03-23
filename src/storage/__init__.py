"""
Storage module - SQLite CRUD operations.
"""

from src.storage.db import (
    get_connection,
    execute,
    create,
    read,
    read_all,
    read_by_ids,
    update,
    delete,
    bulk_create,
    bulk_delete,
    init_file_details_table,
    TABLE_FILE_DETAILS,
)
from src.logger import logger

__all__ = [
    "get_connection",
    "execute",
    "create",
    "read",
    "read_all",
    "read_by_ids",
    "update",
    "delete",
    "bulk_create",
    "bulk_delete",
    "init_file_details_table",
    "TABLE_FILE_DETAILS",
    "logger",
]
