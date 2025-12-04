"""
Request context middleware.

Assigns (or propagates) an `X-Request-ID` header for every HTTP request so that
logs can include a stable correlation identifier.
"""

from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.request_context import clear_request_id, set_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Populate request context (currently only request ID) for every request."""

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        request_id = request.headers.get(self.header_name) or uuid.uuid4().hex
        set_request_id(request_id)

        try:
            response = await call_next(request)
        finally:
            # Always clear the context even if downstream raises.
            clear_request_id()

        response.headers[self.header_name] = request_id
        return response


