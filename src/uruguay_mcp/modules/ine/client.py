"""Thin async client over the ANDA (NADA) JSON API and CKAN fallback.

ANDA is a plain GET-JSON REST API, NOT CKAN, so it does not use the
``{"success": ...}`` unwrap. Search responses carry a ``result`` key; study
metadata responses carry ``{"status": "success", "dataset": {...}}``.
"""

from __future__ import annotations

from typing import Any

from ...shared import cache, errors, http
from .constants import (
    ANDA_CATALOG_URL,
    ANDA_SEARCH_URL,
    API_NAME,
    CKAN_ACTION_URL,
    CKAN_API_NAME,
)


async def search_studies(params: dict[str, Any]) -> tuple[Any, bool, str]:
    """Call ANDA catalog/search and return its ``result`` block (cached)."""
    url = ANDA_SEARCH_URL
    key = "anda:search:" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))

    async def producer() -> Any:
        payload = await http.get_json(url, api=API_NAME, params=params)
        if not isinstance(payload, dict) or "result" not in payload:
            raise errors.upstream(API_NAME, "respuesta de búsqueda inválida")
        return payload["result"]

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


async def get_study(idno: str) -> tuple[Any, bool, str]:
    """Call ANDA catalog/{idno} and return its ``dataset`` block (cached)."""
    url = f"{ANDA_CATALOG_URL}/{idno}"
    key = f"anda:study:{idno}"

    async def producer() -> Any:
        payload = await http.get_json(url, api=API_NAME)
        if not isinstance(payload, dict) or payload.get("status") != "success":
            detail = (payload or {}).get("message", "estudio no encontrado")
            raise errors.upstream(API_NAME, str(detail))
        return payload.get("dataset", {})

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


async def ckan_package_search(params: dict[str, Any]) -> tuple[Any, bool, str]:
    """Call CKAN package_search (organization=ine) and unwrap its result."""
    url = f"{CKAN_ACTION_URL}/package_search"
    key = "ckan:ine:package_search:" + "&".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    async def producer() -> Any:
        payload = await http.get_json(url, api=CKAN_API_NAME, params=params)
        if not isinstance(payload, dict) or not payload.get("success"):
            detail = (payload or {}).get("error", "respuesta inválida")
            raise errors.upstream(CKAN_API_NAME, str(detail))
        return payload["result"]

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url
