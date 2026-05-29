"""Async client for the two Montevideo surfaces.

CKAN surface: public, mirrors the catalogodatos pattern.
Transport surface: OAuth2 client-credentials. A bearer token is minted once
and cached (with the rest of the TTL cache), then sent as an Authorization
header on every ``/api/transportepublico/*`` call.
"""

from __future__ import annotations

from typing import Any

from ...shared import cache, errors, http
from .constants import (
    ACTION_URL,
    CKAN_API_NAME,
    TOKEN_URL,
    TRANSPORT_API_NAME,
    TRANSPORT_BASE_URL,
    client_id,
    client_secret,
)

# OAuth2 tokens from this provider are short-lived; cache them a bit under the
# typical hour so we never serve a stale/expired bearer.
_TOKEN_TTL = 1800
_TOKEN_KEY = "mvd:transport:token"


# --- CKAN -----------------------------------------------------------------
async def _action(action: str, params: dict[str, Any]) -> tuple[Any, bool, str]:
    """Call a CKAN action endpoint and unwrap its result (cached)."""
    url = f"{ACTION_URL}/{action}"
    key = f"mvd-ckan:{action}:" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))

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


async def organization_list(params: dict[str, Any]) -> tuple[Any, bool, str]:
    return await _action("organization_list", params)


async def group_list(params: dict[str, Any]) -> tuple[Any, bool, str]:
    return await _action("group_list", params)


async def datastore_search(params: dict[str, Any]) -> tuple[Any, bool, str]:
    return await _action("datastore_search", params)


# --- Transport (OAuth2) ---------------------------------------------------
async def _access_token() -> str:
    """Return a cached OAuth2 bearer token, minting one if necessary.

    Raises a typed validation error when credentials are not configured, so
    transport tools degrade gracefully instead of hitting a guaranteed 403.
    """
    cid, secret = client_id(), client_secret()
    if not cid or not secret:
        raise errors.ValidationError(
            "Falta configuración: definí URUGUAY_MCP_MVD_CLIENT_ID y "
            "URUGUAY_MCP_MVD_CLIENT_SECRET para usar el transporte de Montevideo.",
            details={"api": TRANSPORT_API_NAME},
        )

    async def producer() -> str:
        data = {
            "grant_type": "client_credentials",
            "client_id": cid,
            "client_secret": secret,
        }
        payload = await http.request_json("POST", TOKEN_URL, api=TRANSPORT_API_NAME, data=data)
        token = (payload or {}).get("access_token") if isinstance(payload, dict) else None
        if not token:
            raise errors.upstream(TRANSPORT_API_NAME, "no se obtuvo access_token")
        return str(token)

    token, _ = await cache.get_or_set(_TOKEN_KEY, producer, ttl=_TOKEN_TTL)
    return token


async def _transport_get(path: str, params: dict[str, Any]) -> tuple[Any, bool, str]:
    """GET a transport endpoint with a bearer token (response cached)."""
    url = f"{TRANSPORT_BASE_URL}/{path}"
    clean = {k: v for k, v in params.items() if v is not None}
    key = f"mvd-tp:{path}:" + "&".join(f"{k}={v}" for k, v in sorted(clean.items()))

    async def producer() -> Any:
        token = await _access_token()
        headers = {"Authorization": f"Bearer {token}"}
        return await http.get_json(
            url, api=TRANSPORT_API_NAME, params=clean, headers=headers
        )

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


def _csv(values: list[str] | list[int] | None) -> str | None:
    if not values:
        return None
    return ",".join(str(v) for v in values)


async def upcoming_buses(
    busstop_id: int,
    lines: list[str],
    amount_per_line: int,
    line_variant_ids: list[int] | None,
) -> tuple[Any, bool, str]:
    params: dict[str, Any] = {
        "lines": _csv(lines),
        "amountperline": amount_per_line,
        "lineVariantIds": _csv(line_variant_ids),
    }
    return await _transport_get(f"buses/busstops/{busstop_id}/upcomingbuses", params)


async def bus_positions(params: dict[str, Any]) -> tuple[Any, bool, str]:
    return await _transport_get("buses", params)


async def buses_geo(center: str, radius_m: float) -> tuple[Any, bool, str]:
    return await _transport_get("buses/geo", {"center": center, "radius": radius_m})


async def list_busstops() -> tuple[Any, bool, str]:
    return await _transport_get("buses/busstops", {})


async def busstop_lines(busstop_id: int) -> tuple[Any, bool, str]:
    return await _transport_get(f"buses/busstops/{busstop_id}/lines", {})
