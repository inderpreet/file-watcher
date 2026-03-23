"""
Logging module using Loguru.
Configured via .env; supports console, file, and extensible sinks (IPC, etc.).
"""

import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# Same format without color markup for file sinks
_LOG_FORMAT_PLAIN = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{name}:{function}:{line} - "
    "{message}"
)

_SINK_IDS: list[int] = []
_CONFIGURED = False


def _parse_level(level: str) -> str:
    """Normalize level string to loguru level name."""
    return level.upper().strip() if level else "INFO"


def configure_logger() -> None:
    """
    Configure the logger from .env and add default sinks.
    Safe to call multiple times; config is applied only once.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    logger.remove()  # Remove default stderr sink; we add our own

    level = _parse_level(os.getenv("LOG_LEVEL", "INFO"))
    log_console = os.getenv("LOG_CONSOLE", "true").lower() in ("true", "1", "yes")
    log_file = os.getenv("LOG_FILE", "").strip()
    log_format = os.getenv("LOG_FORMAT", "").strip() or _LOG_FORMAT
    log_format_plain = os.getenv("LOG_FORMAT_FILE", "").strip() or _LOG_FORMAT_PLAIN

    if log_console:
        sink_id = logger.add(
            sys.stderr,
            level=level,
            format=log_format,
            colorize=True,
        )
        _SINK_IDS.append(sink_id)

    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        rotation = os.getenv("LOG_ROTATION", "10 MB").strip()
        retention = os.getenv("LOG_RETENTION", "7 days").strip()
        sink_id = logger.add(
            path,
            level=level,
            format=log_format_plain,
            colorize=False,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
        )
        _SINK_IDS.append(sink_id)

    _CONFIGURED = True


def add_sink(
    sink: str | Path | Callable[..., Any],
    *,
    level: str = "DEBUG",
    format: str = _LOG_FORMAT_PLAIN,
    **kwargs: Any,
) -> int:
    """
    Add a custom sink for piping logs elsewhere (IPC, queue, remote, etc.).

    Args:
        sink: File path, file-like object, or callable(message).
        level: Minimum level for this sink.
        format: Log format string or use default.
        **kwargs: Additional arguments passed to loguru's add().

    Returns:
        Sink ID for later removal via remove_sink().

    Example:
        # Pipe to a custom handler (e.g., IPC queue)
        def ipc_writer(msg):
            ipc_queue.put(msg)
        add_sink(ipc_writer, level="INFO")
    """
    sink_id = logger.add(sink, level=level, format=format, **kwargs)
    _SINK_IDS.append(sink_id)
    return sink_id


def remove_sink(sink_id: int) -> None:
    """Remove a sink by ID."""
    logger.remove(sink_id)
    if sink_id in _SINK_IDS:
        _SINK_IDS.remove(sink_id)


# Configure on import so all modules get a ready-to-use logger
configure_logger()

__all__ = ["logger", "configure_logger", "add_sink", "remove_sink"]
