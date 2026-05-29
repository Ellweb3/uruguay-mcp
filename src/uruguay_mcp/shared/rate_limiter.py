"""Per-host async token-bucket rate limiter.

Government endpoints are politely shared infrastructure; we cap our own
request rate so a chatty agent never hammers them. One bucket per host.
"""

from __future__ import annotations

import asyncio
import time

from .config import settings


class TokenBucket:
    def __init__(self, rate: float, capacity: float | None = None) -> None:
        self.rate = rate
        self.capacity = capacity or rate
        self._tokens = self.capacity
        self._updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._updated
            self._updated = now
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            if self._tokens < 1:
                wait = (1 - self._tokens) / self.rate
                await asyncio.sleep(wait)
                self._tokens = 0
            else:
                self._tokens -= 1


_buckets: dict[str, TokenBucket] = {}


def bucket_for(host: str) -> TokenBucket:
    if host not in _buckets:
        _buckets[host] = TokenBucket(settings.rate_limit_rps)
    return _buckets[host]
