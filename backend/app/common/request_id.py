"""
Attaches a unique ID to every request. Two jobs:
1. Every response (success or error) includes X-Request-Id, so a client
   or mentor can say "here's the exact request that failed" and you can
   find it in your logs.
2. Logs method/path/status/duration WITHOUT bodies or secrets — per the
   contract's explicit "log it with method/path/status/duration, without
   bodies, secrets or connection strings."
"""

import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.requests")
logging.basicConfig(level=logging.INFO)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-Id"] = request_id

        logger.info(
            "%s %s %s %.1fms request_id=%s",
            request.method, request.url.path, response.status_code, duration_ms, request_id,
        )

        return response