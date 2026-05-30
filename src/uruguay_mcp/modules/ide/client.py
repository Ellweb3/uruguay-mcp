"""Async clients for the two IDE Uruguay surfaces.

WFS surface (GeoServer at mapas.ide.uy):
  - GetCapabilities is XML, fetched as raw text and parsed with the stdlib
    ``xml.etree.ElementTree`` in tools.py;
  - GetFeature is requested with ``outputFormat=application/json`` and returns
    standard GeoJSON, fetched with ``http.get_json``.

Geocoding surface (direcciones.ide.uy): plain JSON arrays via ``http.get_json``.

Each fetch is wrapped in ``cache.get_or_set`` and raises ``errors.upstream`` on
failure. The module stays self-contained (no cross-module imports).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode, urlsplit

import httpx

from ...shared import cache, errors, http
from ...shared.rate_limiter import bucket_for
from .constants import (
    GEO_API_NAME,
    WFS_API_NAME,
    WFS_URL,
    WFS_VERSION,
)


# --- WFS GetCapabilities (raw XML) ---------------------------------------
async def get_capabilities() -> tuple[str, bool, str]:
    """Return ``(xml_text, cached, url)`` for the WFS capabilities document."""
    params = {"service": "WFS", "version": WFS_VERSION, "request": "GetCapabilities"}
    url = f"{WFS_URL}?{urlencode(params)}"
    key = f"ide-wfs:capabilities:{WFS_VERSION}"

    async def producer() -> str:
        host = urlsplit(url).netloc
        await bucket_for(host).acquire()
        client = http.get_client()
        try:
            resp = await client.get(WFS_URL, params=params)
        except httpx.TransportError as exc:
            raise errors.upstream(WFS_API_NAME, str(exc)) from exc
        if resp.status_code >= 400:
            raise errors.upstream(
                WFS_API_NAME, f"HTTP {resp.status_code}", status=resp.status_code
            )
        return resp.text

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


# --- WFS GetFeature (GeoJSON) --------------------------------------------
async def get_feature(params: dict[str, Any]) -> tuple[Any, bool, str]:
    """Call WFS GetFeature and return parsed GeoJSON (cached)."""
    full = {
        "service": "WFS",
        "version": WFS_VERSION,
        "request": "GetFeature",
        **params,
    }
    url = f"{WFS_URL}?{urlencode(full)}"
    key = "ide-wfs:getfeature:" + "&".join(f"{k}={v}" for k, v in sorted(full.items()))

    async def producer() -> Any:
        payload = await http.get_json(WFS_URL, api=WFS_API_NAME, params=full)
        # GeoServer reports a request error as a JSON object with 'exceptions'.
        if isinstance(payload, dict) and payload.get("exceptions"):
            exc = payload["exceptions"]
            detail = exc[0].get("text") if isinstance(exc, list) and exc else str(exc)
            raise errors.upstream(WFS_API_NAME, str(detail))
        return payload

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


# --- Geocoding REST (JSON arrays) ----------------------------------------
async def geocode(endpoint_url: str, params: dict[str, Any]) -> tuple[Any, bool, str]:
    """GET a geocoding endpoint and return its JSON array (cached)."""
    url = f"{endpoint_url}?{urlencode(params)}"
    key = f"ide-geo:{endpoint_url}:" + "&".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    async def producer() -> Any:
        return await http.get_json(endpoint_url, api=GEO_API_NAME, params=params)

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url
