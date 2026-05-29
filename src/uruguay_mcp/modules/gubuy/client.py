"""Thin async client over the CKAN Action API (showcase + package_search).

CKAN responses look like ``{"success": bool, "result": ..., "error": ...}``.
This module normalizes that envelope and raises typed errors on failure.
"""

from __future__ import annotations

from typing import Any

from ...shared import cache, errors, http
from .constants import ACTION_URL, API_NAME


async def _action(action: str, params: dict[str, Any]) -> tuple[Any, bool, str]:
    """Call a CKAN action endpoint and unwrap its result (cached)."""
    url = f"{ACTION_URL}/{action}"
    # Cache key includes sorted params for stable hits across equivalent calls.
    key = f"ckan:{action}:" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))

    async def producer() -> Any:
        payload = await http.get_json(url, api=API_NAME, params=params or None)
        if not isinstance(payload, dict) or not payload.get("success"):
            detail = (payload or {}).get("error", "respuesta inválida")
            raise errors.upstream(API_NAME, str(detail))
        return payload["result"]

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


async def showcase_list() -> tuple[Any, bool, str]:
    # No server-side params honored; returns the full list.
    return await _action("ckanext_showcase_list", {})


async def showcase_show(showcase_id: str) -> tuple[Any, bool, str]:
    return await _action("ckanext_showcase_show", {"id": showcase_id})


async def showcase_package_list(showcase_id: str) -> tuple[Any, bool, str]:
    return await _action("ckanext_showcase_package_list", {"showcase_id": showcase_id})


async def package_search(params: dict[str, Any]) -> tuple[Any, bool, str]:
    return await _action("package_search", params)
