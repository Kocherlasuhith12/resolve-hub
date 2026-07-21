import time
from uuid import UUID, uuid4

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger()


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        supplied = request.headers.get("X-Request-ID")
        try:
            request_id = str(UUID(supplied)) if supplied else str(uuid4())
        except ValueError:
            request_id = str(uuid4())
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "http_request",
            method=request.method,
            route=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
