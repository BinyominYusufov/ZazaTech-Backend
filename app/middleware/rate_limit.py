"""In-memory per-IP rate limiting.

100 req/min per IP overall, 5 req/min per IP on /api/auth/login.
State is a {ip: [timestamps]} dict guarded by an asyncio.Lock; entries
older than the 60s window are pruned on every request.

Note: in-process only — fine for a single-worker deployment. Multiple
workers/instances would each keep their own counters.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

WINDOW_SECONDS = 60
GLOBAL_LIMIT = 100
LOGIN_LIMIT = 5
LOGIN_PATH = "/api/auth/login"


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._general: dict[str, list[float]] = defaultdict(list)
        self._login: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    @staticmethod
    def _prune(bucket: dict[str, list[float]], ip: str, now: float) -> None:
        cutoff = now - WINDOW_SECONDS
        recent = [ts for ts in bucket.get(ip, ()) if ts > cutoff]
        if recent:
            bucket[ip] = recent
        else:
            bucket.pop(ip, None)

    @staticmethod
    def _too_many() -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"success": False, "message": "Too many requests, slow down"},
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = time.monotonic()

        async with self._lock:
            self._prune(self._general, ip, now)
            if len(self._general.get(ip, ())) >= GLOBAL_LIMIT:
                return self._too_many()

            if path == LOGIN_PATH:
                self._prune(self._login, ip, now)
                if len(self._login.get(ip, ())) >= LOGIN_LIMIT:
                    return self._too_many()
                self._login[ip].append(now)

            self._general[ip].append(now)

        return await call_next(request)
