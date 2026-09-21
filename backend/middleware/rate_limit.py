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


DEFAULT_TRUSTED_PROXY_HOPS = 2  # rewrite-ul Vercel + proxy-ul Render


def _client_ip(request: Request, trusted_proxy_hops: int = DEFAULT_TRUSTED_PROXY_HOPS) -> str:
    """
    IP-ul clientului, numărând înapoi prin proxy-urile de încredere.

    În producție cererea trece prin rewrite-ul Vercel și prin proxy-ul Render, deci
    `request.client.host` e IP-ul ultimului proxy: fără antetul de mai jos toți utilizatorii ar
    împărți aceeași fereastră și al 25-lea login dintr-un minut ar pica pentru toată lumea.

    `X-Forwarded-For` e „client, proxy1, proxy2, …", iar fiecare proxy adaugă un element la dreapta.
    Luăm elementul aflat la `trusted_proxy_hops` de la coadă: elementele pe care le-ar putea
    falsifica un client (cele din stânga) nu pot ajunge în acea poziție. Setează
    `RATE_LIMIT_TRUSTED_PROXY_HOPS` să corespundă numărului real de proxy-uri; prea mare înseamnă
    o valoare controlată de client, prea mic înseamnă o fereastră comună.
    """
    forwarded = request.headers.get("x-forwarded-for") or ""
    chain = [part.strip() for part in forwarded.split(",") if part.strip()]
    if chain:
        hops = max(1, trusted_proxy_hops)
        # Lanț mai scurt decât ne așteptam (ex. cerere direct la Render): primul element e tot
        # ce avem, chiar dacă e mai ușor de falsificat.
        return chain[-hops] if len(chain) >= hops else chain[0]
    real_ip = (request.headers.get("x-real-ip") or "").strip()
    if real_ip:
        return real_ip
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
        trusted_proxy_hops: int = DEFAULT_TRUSTED_PROXY_HOPS,
    ):
        super().__init__(app)
        self.enabled = enabled
        self.window_seconds = window_seconds
        self.auth_max_per_window = auth_max_per_window
        self.recommendations_max_per_window = recommendations_max_per_window
        self.trusted_proxy_hops = trusted_proxy_hops

    def _limits_for_path(self, path: str) -> Tuple[int, str] | None:
        if path.startswith("/api/auth"):
            return self.auth_max_per_window, "auth"
        if path.startswith("/api/recommendations"):
            return self.recommendations_max_per_window, "recommendations"
        return None

    def _prune(self, now: float, key: str) -> None:
        cutoff = now - self.window_seconds
        self._hits[key] = [t for t in self._hits[key] if t >= cutoff]
        if not self._hits[key]:
            # Fără asta, dicționarul global ar păstra o cheie per IP văzut vreodată.
            del self._hits[key]

    async def dispatch(self, request: Request, call_next: Callable):
        if not self.enabled or request.method == "OPTIONS":
            return await call_next(request)

        limits = self._limits_for_path(request.url.path)
        if limits is None:
            return await call_next(request)

        max_hits, bucket = limits
        now = time.monotonic()
        ip = _client_ip(request, self.trusted_proxy_hops)
        key = f"{bucket}:{ip}"
        self._prune(now, key)
        if len(self._hits[key]) >= max_hits:
            return JSONResponse(
                status_code=429,
                content={"detail": "Prea multe cereri. Încearcă din nou peste un minut."},
            )
        self._hits[key].append(now)
        return await call_next(request)
