"""Application logging setup (infrastructure)."""
import logging
import os
import sys
from typing import Optional


def configure_logging(level: Optional[int] = None) -> None:
    """Configure root logging for the app (call once at startup).

    In production (ENVIRONMENT=production), emits structured JSON logs to
    stdout so Azure Monitor / Log Analytics can parse and query them natively.
    In development the plain-text format is kept for readability.
    """
    log_level = level if level is not None else logging.INFO

    if logging.root.handlers:
        return

    if os.environ.get("ENVIRONMENT") == "production":
        # Structured JSON logging — requires python-json-logger
        try:
            from pythonjsonlogger import jsonlogger  # type: ignore[import-untyped]
            handler = logging.StreamHandler(sys.stdout)
            formatter = jsonlogger.JsonFormatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s"
            )
            handler.setFormatter(formatter)
            logging.root.setLevel(log_level)
            logging.root.addHandler(handler)
            return
        except ImportError:
            # python-json-logger not installed — fall through to plain-text
            pass

    # Default: human-readable format for local development
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stderr,
    )


def get_logger(name: str = "app") -> logging.Logger:
    """Return a named logger for infrastructure and cross-cutting use."""
    return logging.getLogger(name)


logger = get_logger()
