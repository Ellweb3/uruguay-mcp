"""Thin async client over the BPS 'Observatorio' dashboard backend.

All data endpoints are ``POST`` + JSON and return Elasticsearch-shaped
responses: an array of hits each like ``{"_index": ..., "_source": {...}}``.
This module unwraps ``_source`` from each hit and raises typed errors when the
backend returns ``{"error": ...}`` or a non-list body (e.g. an HTML 500 page).

``series_por_paginas`` is a ``GET`` endpoint that returns ``{"zip": "<base64>"}``
where the base64 decodes to a real ZIP of CSV files.
"""

from __future__ import annotations

from typing import Any

from ...shared import cache, errors, http
from .constants import API_NAME, BASE_URL


def _unwrap_hits(payload: Any) -> list[dict[str, Any]]:
    """Unwrap an Elasticsearch-shaped response into a list of ``_source`` dicts.

    Raises an upstream error when the backend returns ``{"error": ...}`` or any
    non-list body (an HTML 500 page parses as a string, a dict carries the
    error envelope). An empty list is a valid 'no results' answer.
    """
    if isinstance(payload, dict) and "error" in payload:
        raise errors.upstream(API_NAME, str(payload.get("error")))
    if not isinstance(payload, list):
        raise errors.upstream(API_NAME, "respuesta inesperada del backend del Observatorio")
    return [h["_source"] for h in payload if isinstance(h, dict) and "_source" in h]


async def post_hits(endpoint: str, body: dict[str, Any]) -> tuple[list[dict[str, Any]], bool, str]:
    """POST to ``endpoint`` and return its unwrapped ``_source`` hits (cached)."""
    url = f"{BASE_URL}/{endpoint}"
    key = f"bps:{endpoint}:" + "&".join(f"{k}={v}" for k, v in sorted(body.items()))

    async def producer() -> list[dict[str, Any]]:
        payload = await http.request_json("POST", url, api=API_NAME, json=body)
        return _unwrap_hits(payload)

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


async def get_series_zip(id_pagina: int) -> tuple[str, bool, str]:
    """GET ``series_por_paginas`` and return the base64 ZIP string (cached)."""
    url = f"{BASE_URL}/series_por_paginas"
    key = f"bps:series_por_paginas:{id_pagina}"

    async def producer() -> str:
        payload = await http.get_json(url, api=API_NAME, params={"paginas": id_pagina})
        if not isinstance(payload, dict) or not payload.get("zip"):
            raise errors.upstream(API_NAME, "respuesta sin ZIP de series")
        return str(payload["zip"])

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url
