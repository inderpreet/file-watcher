# File Watch

A Python application for file management and backup. Provides a FastAPI REST API, Streamlit dashboard, SQLite storage, and structured logging via Loguru. Configuration is driven by `.env`.

## Project Structure

```
src/
  main.py           # FastAPI entry point (uvicorn)
  streamlit_app.py  # Streamlit dashboard
  api/              # REST API routers (storage, restic, backups)
  logger/           # Loguru-based logging (sinks via .env)
  restic/           # Restic backup integration
  backups/          # Backup wrappers and scripts
  storage/          # SQLite CRUD, file_details table
scripts/
  run_all.py        # Master script (uvicorn + streamlit)
```

## Prerequisites

- Python 3.11+
- [restic](https://restic.net/) installed and on PATH

## Setup

1. Create virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate it:
   - **Windows:** `.venv\Scripts\activate`
   - **Unix:** `source .venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and set your values:
   ```bash
   cp .env.example .env
   ```

## Configuration

Configure the app via `.env`.

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | TRACE, DEBUG, INFO, WARNING, ERROR |
| `LOG_CONSOLE` | `true` | Enable stderr output |
| `LOG_FILE` | - | Path to log file (e.g. `logs/app.log`) |
| `LOG_ROTATION` | `10 MB` | Size or time trigger for rotation |
| `LOG_RETENTION` | `7 days` | How long to keep rotated logs |

### Storage (SQLite)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `data/app.db` | SQLite database file path |

The `file_details` table stores file metadata:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| file_name | TEXT | File name |
| size | INTEGER | Size in bytes |
| hash | TEXT | File hash |
| complete_path | TEXT | Full path (unique) |
| file_created_at | TEXT | File creation datetime (ISO) |
| file_modified_at | TEXT | File modification datetime (ISO) |
| created_at | TIMESTAMP | Record creation time |

### Restic

| Variable | Description |
|----------|-------------|
| `RESTIC_REPOSITORY` | Repository path |
| `RESTIC_PASSWORD` | Repository password |

## Running

### Both (API + Streamlit)

Run API and dashboard together; Ctrl+C stops both:

- **Windows:** `run-all.bat`
- **Unix:** `./run-all.sh`

### FastAPI (REST API only)

Use the convenience scripts (they create the venv if missing):

- **Windows:** `run.bat`
- **Unix:** `./run.sh`

Or run manually:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

- **API:** http://127.0.0.1:8000
- **Interactive docs:** http://127.0.0.1:8000/docs

### Storage API (File Records)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/storage/health` | Database health check |
| POST | `/api/v1/storage/files` | Create single file record |
| GET | `/api/v1/storage/files/{id}` | Get file record by ID |
| GET | `/api/v1/storage/files` | List records (query: path, limit, offset) |
| PUT | `/api/v1/storage/files/{id}` | Update file record |
| DELETE | `/api/v1/storage/files/{id}` | Delete file record |
| POST | `/api/v1/storage/files/bulk` | Bulk create |
| POST | `/api/v1/storage/files/bulk/get` | Bulk get by IDs |
| DELETE | `/api/v1/storage/files/bulk` | Bulk delete by IDs |

### Streamlit (Dashboard)

- **Windows:** `run-streamlit.bat`
- **Unix:** `./run-streamlit.sh`

Or run manually:

```bash
streamlit run src/streamlit_app.py --server.port 8501
```

- **Dashboard:** http://localhost:8501

The dashboard provides a UI for health checks, single-file CRUD, list with filters, and bulk operations.

Rate limiting is applied via SlowAPI (60 requests/minute on the root route).

## Logging

Loguru is configured automatically on import based on `.env`. For custom sinks (IPC, remote, queues), use `add_sink()`:

```python
from src.logger import add_sink, logger

def ipc_callback(msg):
    ipc_queue.put(msg)

add_sink(ipc_callback, level="INFO")
```
