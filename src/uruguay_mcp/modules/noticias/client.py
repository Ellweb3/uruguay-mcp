"""Async client that fetches raw gub.uy HTML (listings + search results).

gub.uy exposes no RSS/Atom/JSON feed, so every surface here is HTML fetched as
raw text via the shared httpx client (mirroring the acce raw-fetch pattern) and
parsed downstream with regex/stdlib. Each fetch is cached per URL and
rate-limited per host (www.gub.uy).
"""

from __future__ import annotations

from urllib.parse import urlencode, urlsplit

import httpx

from ...shared import cache, errors, http
from ...shared.rate_limiter import bucket_for
from .constants import (
    API_NAME,
    BASE_URL,
    LISTING_PATH,
    SEARCH_FIELD,
    SEARCH_PATH,
    SEARCH_SUBSITE_PATH,
)


async def _fetch_html(url: str, key: str) -> tuple[str, bool, str]:
    """Return ``(html_text, cached, url)`` for a public gub.uy page."""

    async def producer() -> str:
        host = urlsplit(url).netloc
        await bucket_for(host).acquire()
        client = http.get_client()
        try:
            resp = await client.get(url)
        except httpx.TransportError as exc:
            raise errors.upstream(API_NAME, str(exc)) from exc
        if resp.status_code >= 400:
            raise errors.upstream(API_NAME, f"HTTP {resp.status_code}", status=resp.status_code)
        return resp.text

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


async def fetch_listing(subsite: str, page: int) -> tuple[str, bool, str]:
    """Fetch a /{subsite}/comunicacion/noticias listing page (0-based)."""
    path = LISTING_PATH.format(subsite=subsite)
    url = f"{BASE_URL}{path}"
    if page:
        url = f"{url}?{urlencode({'page': page})}"
    return await _fetch_html(url, f"noticias-listing:{subsite}:{page}")


async def fetch_search(query: str, subsite: str | None) -> tuple[str, bool, str]:
    """Fetch the Drupal Search API results page for ``query``."""
    path = SEARCH_SUBSITE_PATH.format(subsite=subsite) if subsite else SEARCH_PATH
    url = f"{BASE_URL}{path}?{urlencode({SEARCH_FIELD: query})}"
    key = f"noticias-search:{subsite or ''}:{query}"
    return await _fetch_html(url, key)
