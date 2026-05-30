"""Thin async client over the CKAN Action API, scoped to ANEP.

Self-contained: it re-implements the catalogodatos ``_action`` pattern with its
own ACTION_URL/API_NAME so the module does not import other modules. CKAN
responses look like ``{"success": bool, "result": ..., "error": ...}``; this
normalizes that envelope and raises typed errors on failure.
"""

from __future__ import annotations

from typing import Any

from ...shared import cache, errors, http
from .constants import ACTION_URL, API_NAME

# Substring CKAN datastore returns (HTTP 404 body) for resources without an
# active datastore. We map it to a typed NotFoundError.
_NO_DATASTORE_HINT = "datastoreentitydoesnotexist"


async def _action(action: str, params: dict[str, Any]) -> tuple[Any, bool, str]:
    """Call a CKAN action endpoint and unwrap its result (cached)."""
    url = f"{ACTION_URL}/{action}"
    key = f"educacion-ckan:{action}:" + "&".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    async def producer() -> Any:
        payload = await http.get_json(url, api=API_NAME, params=params)
        if not isinstance(payload, dict) or not payload.get("success"):
            detail = (payload or {}).get("error", "respuesta inválida")
            raise errors.upstream(API_NAME, str(detail))
        return payload["result"]

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


async def package_search(params: dict[str, Any]) -> tuple[Any, bool, str]:
    return await _action("package_search", params)


async def package_show(dataset_id: str) -> tuple[Any, bool, str]:
    return await _action("package_show", {"id": dataset_id})


async def datastore_search(params: dict[str, Any]) -> tuple[Any, bool, str]:
    """Query a resource datastore, mapping 'no datastore' to NotFoundError.

    Download-only resources (no active datastore) answer with an error body
    whose type mentions ``DatastoreEntityDoesNotExist``. We surface that as a
    typed not-found error so callers can fall back to the resource URL.
    """
    url = f"{ACTION_URL}/datastore_search"
    key = "educacion-ckan:datastore_search:" + "&".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    async def producer() -> Any:
        payload = await http.get_json(url, api=API_NAME, params=params)
        if not isinstance(payload, dict) or not payload.get("success"):
            err = (payload or {}).get("error", {})
            blob = str(err).lower()
            if _NO_DATASTORE_HINT in blob or "not found" in blob:
                raise errors.NotFoundError(
                    "El recurso no tiene datastore activo (solo descarga).",
                    details={"api": API_NAME},
                )
            raise errors.upstream(API_NAME, str(err or "respuesta inválida"))
        return payload["result"]

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url
