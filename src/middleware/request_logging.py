"""HTTP request logging: method, path, start time (UTC), duration, status."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from starlette.requests import Request

logger = logging.getLogger("http.request")


def _path_with_query(request: Request) -> str:
    path = request.url.path
    if request.url.query:
        return f"{path}?{request.url.query}"
    return path


async def request_logging_middleware(request: Request, call_next):
    started_mono = time.perf_counter()
    started_at = datetime.now(timezone.utc)
    method = request.method
    path = _path_with_query(request)
    ts = started_at.isoformat().replace("+00:00", "Z")
    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started_mono) * 1000
        logger.info(
            "%s %s %s status=%s duration_ms=%.2f",
            ts,
            method,
            path,
            response.status_code,
            duration_ms,
        )
        return response
    except Exception:
        duration_ms = (time.perf_counter() - started_mono) * 1000
        logger.exception(
            "%s %s %s failed duration_ms=%.2f",
            ts,
            method,
            path,
            duration_ms,
        )
        raise
