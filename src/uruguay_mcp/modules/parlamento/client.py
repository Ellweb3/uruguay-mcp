"""Thin async client for the Parlamento del Uruguay surfaces.

CKAN surface: org-scoped reads against catalogodatos.gub.uy. We keep our own
tiny ``_action`` (copying the catalogodatos pattern) so the module stays
self-contained and always injects ``fq=organization:parlamento-uruguayo``.

CKAN responses look like ``{"success": bool, "result": ..., "error": ...}``;
this normalizes that envelope and raises typed errors on failure.
"""

from __future__ import annotations

from typing import Any

from ...shared import cache, errors, http
from .constants import ACTION_URL, CKAN_API_NAME


async def _action(action: str, params: dict[str, Any]) -> tuple[Any, bool, str]:
    """Call a CKAN action endpoint and unwrap its result (cached)."""
    url = f"{ACTION_URL}/{action}"
    # Cache key includes sorted params for stable hits across equivalent calls.
    key = f"parl-ckan:{action}:" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))

    async def producer() -> Any:
        payload = await http.get_json(url, api=CKAN_API_NAME, params=params)
        if not isinstance(payload, dict) or not payload.get("success"):
            detail = (payload or {}).get("error", "respuesta inválida")
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
