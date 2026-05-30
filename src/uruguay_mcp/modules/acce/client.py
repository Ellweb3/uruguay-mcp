"""Async clients for the two ACCE surfaces.

OCDS surface (plain HTTP, no auth):
  - the RSS feed is XML, so we fetch raw text via the shared httpx client and
    parse it with the stdlib ``xml.etree.ElementTree``;
  - record/release packages are JSON, fetched with ``http.get_json``.

CKAN surface mirrors the catalogodatos ``_action`` pattern but is scoped to the
ACCE organization. The module stays self-contained (no cross-module imports).
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
    OCDS_API_NAME,
    RECORD_URL,
    RELEASE_URL,
    RSS_URL,
)

# Leading-space message returned (with a 404) for unknown record/release ids.
_NOT_FOUND_HINT = "no se encuentra"


# --- OCDS RSS (raw XML) ---------------------------------------------------
async def fetch_rss(year: int | None, month: int | None) -> tuple[str, bool, str]:
    """Return ``(xml_text, cached, url)`` for the RSS feed.

    With both ``year`` and ``month`` the monthly variant is used; otherwise the
    latest feed (~500 releases). The body is RSS 2.0 despite the atom mime type.
    """
    url = RSS_URL
    if year is not None and month is not None:
        url = f"{RSS_URL}/{year}/{month:02d}"
    key = f"acce-rss:{url}"

    async def producer() -> str:
        host = urlsplit(url).netloc
        await bucket_for(host).acquire()
        client = http.get_client()
        try:
            resp = await client.get(url)
        except httpx.TransportError as exc:
            raise errors.upstream(OCDS_API_NAME, str(exc)) from exc
        if resp.status_code >= 400:
            raise errors.upstream(
                OCDS_API_NAME, f"HTTP {resp.status_code}", status=resp.status_code
            )
        return resp.text

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


# --- OCDS JSON (record / release) ----------------------------------------
async def _ocds_json(url: str, key: str) -> tuple[Any, bool, str]:
    """GET an OCDS JSON package, mapping 404 bodies to a not-found error."""

    async def producer() -> Any:
        host = urlsplit(url).netloc
        await bucket_for(host).acquire()
        client = http.get_client()
        try:
            resp = await client.get(url)
        except httpx.TransportError as exc:
            raise errors.upstream(OCDS_API_NAME, str(exc)) from exc
        if resp.status_code == 404:
            raise errors.NotFoundError(
                f"El identificador especificado no se encuentra en ACCE: {url}",
                details={"api": OCDS_API_NAME, "status": 404},
            )
        if resp.status_code >= 400:
            raise errors.upstream(
                OCDS_API_NAME, f"HTTP {resp.status_code}", status=resp.status_code
            )
        try:
            payload = resp.json()
        except ValueError as exc:
            raise errors.upstream(OCDS_API_NAME, "respuesta no es JSON válido") from exc
        # Some unknown ids answer 200 with an error body instead of a 404.
        if isinstance(payload, dict) and _NOT_FOUND_HINT in str(payload.get("message", "")):
            raise errors.NotFoundError(
                "El identificador especificado no se encuentra en ACCE.",
                details={"api": OCDS_API_NAME},
            )
        return payload

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


async def get_record(idcompra: str) -> tuple[Any, bool, str]:
    url = f"{RECORD_URL}/{idcompra}"
    return await _ocds_json(url, f"acce-record:{idcompra}")


async def get_release(param: str) -> tuple[Any, bool, str]:
    url = f"{RELEASE_URL}/{param}"
    return await _ocds_json(url, f"acce-release:{param}")


# --- CKAN (scoped to organization:acce) ----------------------------------
async def package_search(params: dict[str, Any]) -> tuple[Any, bool, str]:
    """Call CKAN ``package_search`` and unwrap its result (cached)."""
    url = f"{CKAN_ACTION_URL}/package_search"
    key = "acce-ckan:package_search:" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))

    async def producer() -> Any:
        payload = await http.get_json(url, api=CKAN_API_NAME, params=params)
        if not isinstance(payload, dict) or not payload.get("success"):
            detail = (payload or {}).get("error", "respuesta inválida")
            raise errors.upstream(CKAN_API_NAME, str(detail))
        return payload["result"]

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url
