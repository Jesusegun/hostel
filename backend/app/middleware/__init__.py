"""
Middleware package.

Holds reusable Starlette/FastAPI middleware classes that implement cross-cutting
concerns such as request tracing.
"""

from app.middleware.request_context import RequestContextMiddleware

__all__ = ["RequestContextMiddleware"]


