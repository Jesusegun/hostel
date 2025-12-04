"""
Request context utilities.

Provides helpers to store and retrieve per-request metadata such as the
current request identifier for structured logging and tracing purposes.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional


_request_id_ctx_var: ContextVar[Optional[str]] = ContextVar(
    "request_id", default=None
)


def set_request_id(request_id: str) -> None:
    """Store the active request ID in the context."""
    _request_id_ctx_var.set(request_id)


def get_request_id() -> Optional[str]:
    """Return the current request ID (or None if not set)."""
    return _request_id_ctx_var.get()


def clear_request_id() -> None:
    """Clear the request ID from the context (used after responses complete)."""
    _request_id_ctx_var.set(None)


