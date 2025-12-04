"""
Application logging configuration.

Configures structured logging with request identifiers so that log lines can be
correlated across services and background jobs.
"""

from __future__ import annotations

import logging
import logging.config
from typing import Any, Dict

from app.utils.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    """Inject the current request ID (if any) into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "n/a"
        return True


def configure_logging() -> None:
    """Configure application-wide logging."""
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {
                "()": RequestIdFilter,
            }
        },
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "filters": ["request_id"],
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)


