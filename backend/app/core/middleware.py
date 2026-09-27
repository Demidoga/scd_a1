"""Request-ID propagation + access logging + request metrics.

One ASGI middleware doing three things at once, in the order the assignment
cares about: (1) establish request_id from X-Request-ID or generate one,
(2) log request start/end as structured JSON, (3) record Prometheus request
count/latency. docs/architecture/backend.md §6.
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, request_id_var
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_var.set(request_id)
        start = time.perf_counter()

        # request_id_var must stay set for every log call below, including the
        # exception path, so it's only reset in `finally` — after logging.
        try:
            response = await call_next(request)
        except Exception:
            duration = time.perf_counter() - start
            logger.exception(
                "request_failed", method=request.method, path=request.url.path, duration_s=duration
            )
            raise
        else:
            duration = time.perf_counter() - start
            route = request.scope.get("route")
            path_label = route.path_format if route is not None else request.url.path

            REQUEST_COUNT.labels(
                method=request.method, path=path_label, status_code=response.status_code
            ).inc()
            REQUEST_LATENCY.labels(method=request.method, path=path_label).observe(duration)

            response.headers["X-Request-ID"] = request_id
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_s=round(duration, 4),
            )
            return response
        finally:
            request_id_var.reset(token)
