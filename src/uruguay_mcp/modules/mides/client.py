"""Async clients for the two MIDES surfaces.

CKAN surface mirrors the catalogodatos ``_action`` pattern but is scoped to the
MIDES organization. CKAN replies with ``{"success": bool, "result": ...}`` and
HTTP 200 even for unknown ids (``error.__type == 'Not Found Error'``), so we
normalize that into a typed :class:`NotFoundError`.

Guía Nacional de Recursos Sociales has no JSON API: it is an Innova/Oracle
WebCenter JSP portal. We fetch raw HTML via the shared httpx client (like
``acce.fetch_rss``) and the tool layer scrapes the canonical resource links.

The module stays self-contained (no cross-module imports).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import httpx

from ...shared import cache, errors, http
from ...shared.rate_limiter import bucket_for
from .constants import (
    CKAN_ACTION_URL,
    CKAN_API_NAME,
    GUIA_API_NAME,
    GUIA_SEARCH_URL,
)


# --- CKAN (scoped to organization:mides) ---------------------------------
async def _action(action: str, params: dict[str, Any]) -> tuple[Any, bool, str]:
    """Call a CKAN action endpoint and unwrap its result (cached)."""
    url = f"{CKAN_ACTION_URL}/{action}"
    key = f"mides-ckan:{action}:" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))

    async def producer() -> Any:
        payload = await http.get_json(url, api=CKAN_API_NAME, params=params)
        if not isinstance(payload, dict) or not payload.get("success"):
            error = (payload or {}).get("error") or {}
            etype = error.get("__type") if isinstance(error, dict) else None
            if etype == "Not Found Error":
                raise errors.NotFoundError(
                    "El recurso solicitado no existe en el catálogo (MIDES).",
                    details={"api": CKAN_API_NAME},
                )
            detail = error or "respuesta inválida"
            raise errors.upstream(CKAN_API_NAME, str(detail))
        return payload["result"]

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


async def package_search(params: dict[str, Any]) -> tuple[Any, bool, str]:
    return await _action("package_search", params)


async def package_show(dataset_id: str) -> tuple[Any, bool, str]:
    return await _action("package_show", {"id": dataset_id})


async def datastore_search(params: dict[str, Any]) -> tuple[Any, bool, str]:
    return await _action("datastore_search", params)


# --- Guía Nacional de Recursos Sociales (raw HTML scrape) ----------------
async def fetch_guia(params: dict[str, Any]) -> tuple[str, bool, str]:
    """Return ``(html_text, cached, url)`` for a Guía de Recursos search.

    The JSP portal answers text/html (no JSON variant exists) and sets an
    anonymous session cookie that httpx handles automatically via redirects.
    """
    url = GUIA_SEARCH_URL
    key = "mides-guia:" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))

    async def producer() -> str:
        host = urlsplit(url).netloc
        await bucket_for(host).acquire()
        client = http.get_client()
        try:
            resp = await client.get(url, params=params)
        except httpx.TransportError as exc:
            raise errors.upstream(GUIA_API_NAME, str(exc)) from exc
        if resp.status_code >= 400:
            raise errors.upstream(
                GUIA_API_NAME, f"HTTP {resp.status_code}", status=resp.status_code
            )
        return resp.text

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url
