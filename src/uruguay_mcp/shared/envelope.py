"""Unified response envelope.

Every tool returns the same shape so the model always knows where data came
from, whether it was served from cache, and in what language. Mirrors the
``{_meta, data}`` convention used by mature government-data MCP servers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .config import settings


def envelope(
    data: Any,
    *,
    api: str,
    url: str | None = None,
    cached: bool = False,
    lang: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Wrap ``data`` in the standard envelope.

    Stamps a UTC ISO-8601 ``timestamp`` into ``_meta`` so every response carries
    its generation time.
    """
    meta: dict[str, Any] = {
        "source": {"api": api, "url": url},
        "cached": cached,
        "lang": lang or settings.lang,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if extra:
        meta.update(extra)
    return {"_meta": meta, "data": data}


def error_envelope(
    code: str, message: str, *, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Standard envelope for a failed call."""
    return {
        "_meta": {"ok": False, "lang": settings.lang},
        "error": {"code": code, "message": message, "details": details or {}},
    }
