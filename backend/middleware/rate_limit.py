"""
Rate limiting simplu în memorie (per proces) pentru rute sensibile.
Pentru producție multi-worker, folosește Redis sau gateway (Cloudflare, nginx).
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable, DefaultDict, List, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


def _client_ip(request: Request) -> str:
    """
    IP-ul real al clientului.

    În producție aplicația stă în spatele a două proxy-uri (rewrite-ul Vercel → Render), deci
    `request.client.host` e IP-ul proxy-ului: fără antetul de mai jos toți utilizatorii ar împărți
    aceeași fereastră de rate limit și al 25-lea login dintr-un minut ar pica pentru toată lumea.
    Primul element din `X-Forwarded-For` e clientul original (poate fi falsificat, dar aici e folosit
    doar ca să separe ferestrele, nu ca decizie de securitate).
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    real_ip = request.headers.get("x-real-ip")
    if real_ip and real_ip.strip():
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window aproximativ: max N cereri / minut / IP pe prefixe selectate."""

    _hits: DefaultDict[str, List[float]] = defaultdict(list)

    def __init__(
        self,
        app,
        *,
        enabled: bool = True,
        window_seconds: float = 60.0,
        auth_max_per_window: int = 24,
        recommendations_max_per_window: int = 45,
    ):
        super().__init__(app)
        self.enabled = enabled
        self.window_seconds = window_seconds
        self.auth_max_per_window = auth_max_per_window
        self.recommendations_max_per_window = recommendations_max_per_window

    def _limits_for_path(self, path: str) -> Tuple[int, str] | None:
        if path.startswith("/api/auth"):
            return self.auth_max_per_window, "auth"
        if path.startswith("/api/recommendations"):
            return self.recommendations_max_per_window, "recommendations"
        return None

    def _prune(self, now: float, key: str) -> None:
        cutoff = now - self.window_seconds
        self._hits[key] = [t for t in self._hits[key] if t >= cutoff]

    async def dispatch(self, request: Request, call_next: Callable):
        if not self.enabled or request.method == "OPTIONS":
            return await call_next(request)

        limits = self._limits_for_path(request.url.path)
        if limits is None:
            return await call_next(request)

        max_hits, bucket = limits
        now = time.monotonic()
        ip = _client_ip(request)
        key = f"{bucket}:{ip}"
        self._prune(now, key)
        if len(self._hits[key]) >= max_hits:
            return JSONResponse(
                status_code=429,
                content={"detail": "Prea multe cereri. Încearcă din nou peste un minut."},
            )
        self._hits[key].append(now)
        return await call_next(request)
