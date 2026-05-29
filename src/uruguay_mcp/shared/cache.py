"""Tiny async TTL cache.

A process-local in-memory cache is plenty for an MCP server: it collapses
repeated identical lookups within a session without any external dependency.
Keyed by a caller-supplied string; values expire after ``settings.cache_ttl``.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from .config import settings

_store: dict[str, tuple[float, Any]] = {}
_lock = asyncio.Lock()


def _now() -> float:
    return time.monotonic()


async def get_or_set(
    key: str, producer: Callable[[], Awaitable[Any]], *, ttl: int | None = None
) -> tuple[Any, bool]:
    """Return ``(value, cached)``. Calls ``producer`` on miss/expiry.

    The producer runs outside the lock so slow upstream calls don't serialize
    unrelated cache access.
    """
    ttl = ttl if ttl is not None else settings.cache_ttl
    async with _lock:
        hit = _store.get(key)
        if hit and (_now() - hit[0]) < ttl:
            return hit[1], True

    value = await producer()

    async with _lock:
        _store[key] = (_now(), value)
    return value, False


def clear() -> None:
    _store.clear()
