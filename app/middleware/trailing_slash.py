"""Trailing-slash normalization.

Rewrites `/path/` -> `/path` in the ASGI scope *before* routing, so both
`/api/services` and `/api/services/` hit the same handler with a 200 and
no 307 redirect. Pure-ASGI (not BaseHTTPMiddleware) because the path must
be changed before the router matches it.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send


class TrailingSlashMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] == "http":
            path: str = scope.get("path", "")
            if len(path) > 1 and path.endswith("/"):
                normalized = path.rstrip("/") or "/"
                scope = dict(scope)
                scope["path"] = normalized
                raw_path = scope.get("raw_path")
                if raw_path:
                    # raw_path excludes the query string per the ASGI spec.
                    scope["raw_path"] = raw_path.rstrip(b"/") or b"/"
        await self.app(scope, receive, send)
