"""Simple in-process sliding-window rate limiter.

Adequate for a single API instance (pilot). For horizontally scaled deployments replace with a
shared store (e.g. Redis) — documented in docs/DEPLOYMENT.md.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_s: float = 60.0) -> bool:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > window_s:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            if len(self._hits) > 50_000:  # bound memory under abuse
                for k in list(self._hits)[:10_000]:
                    if not self._hits[k] or now - self._hits[k][-1] > window_s:
                        self._hits.pop(k, None)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    from .config import get_settings

    n = get_settings().trusted_proxy_count
    if n > 0:
        fwd = request.headers.get("x-forwarded-for", "")
        parts = [p.strip() for p in fwd.split(",") if p.strip()]
        if len(parts) >= n:
            return parts[-n]
    return request.client.host if request.client else "unknown"


def enforce(request: Request, bucket: str, limit: int, window_s: float = 60.0, key_extra: str = "") -> None:
    key = f"{bucket}:{client_ip(request)}:{key_extra}"
    if not limiter.check(key, limit, window_s):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests. Please wait and try again.")
