"""Loguru-based structured logging."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger as _logger

_configured = False


def setup_logging(level: str = "INFO", log_dir: Path | str | None = None) -> None:
    """Configure loguru sinks. Idempotent."""
    global _configured
    if _configured:
        return

    _logger.remove()
    _logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <7}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    if log_dir is not None:
        log_path = Path(log_dir) / "trading_analysis.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        _logger.add(
            log_path,
            level=level,
            rotation="10 MB",
            retention=10,
            compression="zip",
            enqueue=True,
        )

    _configured = True


def get_logger(name: str | None = None):
    """Get a loguru logger, optionally bound to a name."""
    if not _configured:
        setup_logging()
    return _logger.bind(name=name) if name else _logger
