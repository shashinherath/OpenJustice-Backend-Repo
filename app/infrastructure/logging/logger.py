"""Application logging setup (infrastructure)."""
import logging
import sys
from typing import Optional


def configure_logging(level: Optional[int] = None) -> None:
    """Configure root logging for the app (call once at startup)."""
    log_level = level if level is not None else logging.INFO
    if not logging.root.handlers:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            stream=sys.stderr,
        )


def get_logger(name: str = "app") -> logging.Logger:
    """Return a named logger for infrastructure and cross-cutting use."""
    return logging.getLogger(name)


logger = get_logger()
