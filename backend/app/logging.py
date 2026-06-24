"""Basic logging configuration."""

import logging
import sys

from app.config import settings


def configure_logging() -> None:
    """Configure root logger for the application."""
    level = logging.DEBUG if settings.is_development else logging.INFO
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
