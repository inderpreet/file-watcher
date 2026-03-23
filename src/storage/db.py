"""
SQLite database connection and generic CRUD operations.
"""

import sqlite3
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
import os

from src.logger import logger

load_dotenv()

_DEFAULT_DB = "data/app.db"

# Table for file details
TABLE_FILE_DETAILS = "file_details"

_FILE_DETAILS_SCHEMA = """
CREATE TABLE IF NOT EXISTS file_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    size INTEGER NOT NULL,
    hash TEXT NOT NULL,
    complete_path TEXT NOT NULL,
    file_created_at TEXT,
    file_modified_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(complete_path)
)
"""

# Table for RESTIC backup logs
TABLE_RESTIC_LOGS = "restic_logs"

_RESTIC_LOGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS restic_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_name TEXT NOT NULL,
    source_paths TEXT NOT NULL,
    dest_path TEXT NOT NULL,
    status TEXT NOT NULL,
    stdout TEXT,
    stderr TEXT,
    return_code INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
)
"""


def _table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def init_file_details_table() -> None:
    """Create the file_details table if it does not exist, and migrate existing tables."""
    execute(_FILE_DETAILS_SCHEMA.strip())
    conn = get_connection()
    try:
        if _table_has_column(conn, TABLE_FILE_DETAILS, "file_created_at"):
            return
        conn.execute("ALTER TABLE file_details ADD COLUMN file_created_at TEXT")
        conn.execute("ALTER TABLE file_details ADD COLUMN file_modified_at TEXT")
        conn.commit()
        logger.debug("Added file_created_at, file_modified_at to file_details")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            pass
        else:
            raise
    finally:
        conn.close()
    logger.debug("Ensured file_details table exists")


def init_restic_logs_table() -> None:
    """Create the restic_logs table if it does not exist."""
    execute(_RESTIC_LOGS_SCHEMA.strip())
    logger.debug("Ensured restic_logs table exists")


def _get_db_path() -> Path:
    """Resolve database path from env or default."""
    path = os.getenv("DATABASE_PATH", _DEFAULT_DB).strip()
    return Path(path)


def get_connection() -> sqlite3.Connection:
    """Open and return a database connection. Sets row_factory to sqlite3.Row."""
    path = _get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def execute(sql: str, params: tuple = ()) -> None:
    """Execute raw SQL. Use for CREATE TABLE, migrations, etc."""
    with get_connection() as conn:
        conn.execute(sql, params)
        conn.commit()
    logger.debug("Executed SQL: {}...", sql.strip()[:50])


def create(table: str, data: dict[str, Any]) -> int:
    """
    Insert a row and return the last row ID.

    Args:
        table: Table name.
        data: Dict of column -> value.

    Returns:
        Last inserted row ID.
    """
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    with get_connection() as conn:
        cur = conn.execute(sql, list(data.values()))
        conn.commit()
        row_id = cur.lastrowid or 0
    logger.debug("Created row in {}: id={}", table, row_id)
    return row_id


def read(
    table: str,
    id_column: str = "id",
    id_value: Any = None,
    *,
    where: Optional[str] = None,
    params: Optional[tuple] = None,
) -> Optional[sqlite3.Row]:
    """
    Read a single row by ID or custom WHERE clause.

    Args:
        table: Table name.
        id_column: Primary key column (used when id_value is set).
        id_value: Value for id_column lookup.
        where: Custom WHERE clause (e.g. "status = ?").
        params: Parameters for WHERE clause.

    Returns:
        Row as sqlite3.Row or None.
    """
    conn = get_connection()
    cur = conn.cursor()
    if id_value is not None:
        cur.execute(f"SELECT * FROM {table} WHERE {id_column} = ?", (id_value,))
    elif where and params is not None:
        cur.execute(f"SELECT * FROM {table} WHERE {where}", params)
    else:
        cur.execute(f"SELECT * FROM {table} LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row


def read_all(
    table: str,
    *,
    where: Optional[str] = None,
    params: Optional[tuple] = None,
    order_by: Optional[str] = None,
) -> list[sqlite3.Row]:
    """
    Read all rows from a table.

    Args:
        table: Table name.
        where: Optional WHERE clause.
        params: Parameters for WHERE.
        order_by: Optional ORDER BY clause.

    Returns:
        List of rows.
    """
    sql = f"SELECT * FROM {table}"
    query_params: tuple = ()
    if where and params is not None:
        sql += f" WHERE {where}"
        query_params = params
    if order_by:
        sql += f" ORDER BY {order_by}"
    with get_connection() as conn:
        cur = conn.execute(sql, query_params)
        return list(cur.fetchall())


def update(
    table: str,
    id_column: str,
    id_value: Any,
    data: dict[str, Any],
) -> int:
    """
    Update a row by ID.

    Args:
        table: Table name.
        id_column: Primary key column.
        id_value: Primary key value.
        data: Dict of column -> new value.

    Returns:
        Number of rows updated.
    """
    set_clause = ", ".join(f"{k} = ?" for k in data.keys())
    sql = f"UPDATE {table} SET {set_clause} WHERE {id_column} = ?"
    values = list(data.values()) + [id_value]
    with get_connection() as conn:
        cur = conn.execute(sql, values)
        conn.commit()
        count = cur.rowcount
    logger.debug("Updated {} rows in {}", count, table)
    return count


def delete(table: str, id_column: str, id_value: Any) -> int:
    """
    Delete a row by ID.

    Args:
        table: Table name.
        id_column: Primary key column.
        id_value: Primary key value.

    Returns:
        Number of rows deleted.
    """
    sql = f"DELETE FROM {table} WHERE {id_column} = ?"
    with get_connection() as conn:
        cur = conn.execute(sql, (id_value,))
        conn.commit()
        count = cur.rowcount
    logger.debug("Deleted {} rows from {}", count, table)
    return count


def bulk_create(table: str, rows: list[dict[str, Any]]) -> list[int]:
    """
    Insert multiple rows. Returns list of inserted row IDs.
    """
    if not rows:
        return []
    ids = []
    with get_connection() as conn:
        for data in rows:
            columns = ", ".join(data.keys())
            placeholders = ", ".join("?" * len(data))
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cur = conn.execute(sql, list(data.values()))
            ids.append(cur.lastrowid or 0)
        conn.commit()
    logger.debug("Bulk created {} rows in {}", len(ids), table)
    return ids


def read_by_ids(table: str, id_column: str, id_values: list[Any]) -> list[sqlite3.Row]:
    """Read rows by list of IDs."""
    if not id_values:
        return []
    placeholders = ", ".join("?" * len(id_values))
    sql = f"SELECT * FROM {table} WHERE {id_column} IN ({placeholders})"
    with get_connection() as conn:
        cur = conn.execute(sql, id_values)
        return list(cur.fetchall())


def bulk_delete(table: str, id_column: str, id_values: list[Any]) -> int:
    """
    Delete rows by IDs. Returns number of rows deleted.
    """
    if not id_values:
        return 0
    placeholders = ", ".join("?" * len(id_values))
    sql = f"DELETE FROM {table} WHERE {id_column} IN ({placeholders})"
    with get_connection() as conn:
        cur = conn.execute(sql, id_values)
        conn.commit()
        count = cur.rowcount
    logger.debug("Bulk deleted {} rows from {}", count, table)
    return count
