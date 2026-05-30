"""Thin async CKAN client for the health (salud) module.

Self-contained copy of the catalogodatos ``_action`` pattern (own ACTION_URL /
API_NAME) so the module has no cross-module imports. CKAN responses look like
``{"success": bool, "result": ..., "error": ...}``; this normalizes that
envelope and raises typed errors on failure.

A separate helper fetches a raw CSV (the policlínicas resource is not
datastore-active) via ``http._request`` like impo/acce did.
"""

from __future__ import annotations

from typing import Any

import httpx

from ...shared import cache, errors, http
from .constants import ACTION_URL, API_NAME


async def _action(action: str, params: dict[str, Any]) -> tuple[Any, bool, str]:
    """Call a CKAN action endpoint and unwrap its result (cached)."""
    url = f"{ACTION_URL}/{action}"
    # Cache key includes sorted params for stable hits across equivalent calls.
    key = f"salud-ckan:{action}:" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))

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
    return await _action("datastore_search", params)


async def datastore_search_sql(sql: str) -> tuple[Any, bool, str]:
    return await _action("datastore_search_sql", {"sql": sql})


async def fetch_csv(url: str) -> tuple[str, bool, str]:
    """GET a raw CSV resource (e.g. policlínicas) as text (cached).

    The policlínicas CSV is not datastore-active, so it cannot be queried via
    datastore_search; we download and parse it client-side instead. Uses the
    shared ``_request`` directly so a non-JSON body is fetched as raw text.
    """
    key = f"salud-csv:{url}"

    async def producer() -> str:
        try:
            resp = await http._request("GET", url, api=API_NAME)
        except http._RetryableStatus as exc:
            raise errors.upstream(API_NAME, str(exc)) from exc
        except httpx.TransportError as exc:
            raise errors.upstream(API_NAME, str(exc)) from exc
        if resp.status_code >= 400:
            raise errors.upstream(
                API_NAME, f"HTTP {resp.status_code}", status=resp.status_code
            )
        return resp.text

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url
