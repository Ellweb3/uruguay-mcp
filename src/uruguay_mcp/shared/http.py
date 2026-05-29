"""Shared async HTTP client with retries and rate limiting.

A single lazily-created :class:`httpx.AsyncClient` is reused for connection
pooling. Every request is rate-limited per host and retried on transient
failures (timeouts, connection errors, 5xx, 429) with exponential backoff.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from . import errors
from .config import settings
from .rate_limiter import bucket_for

_client: httpx.AsyncClient | None = None

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=settings.http_timeout,
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
        )
    return _client


async def aclose() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


class _RetryableStatus(Exception):
    """Internal signal to trigger a tenacity retry on a retryable HTTP status."""


@retry(
    retry=retry_if_exception_type((httpx.TransportError, _RetryableStatus)),
    stop=stop_after_attempt(settings.http_max_retries),
    wait=wait_exponential(multiplier=0.5, max=8),
    reraise=True,
)
async def _request(method: str, url: str, *, api: str, **kwargs: Any) -> httpx.Response:
    host = urlsplit(url).netloc
    await bucket_for(host).acquire()
    client = get_client()
    resp = await client.request(method, url, **kwargs)
    if resp.status_code in _RETRYABLE_STATUS:
        raise _RetryableStatus(f"{resp.status_code} from {api}")
    return resp


async def request_json(method: str, url: str, *, api: str, **kwargs: Any) -> Any:
    """Perform a request and return parsed JSON, raising :class:`UpstreamError`."""
    try:
        resp = await _request(method, url, api=api, **kwargs)
    except (httpx.TransportError, _RetryableStatus) as exc:
        raise errors.upstream(api, str(exc)) from exc

    if resp.status_code >= 400:
        raise errors.upstream(api, f"HTTP {resp.status_code}", status=resp.status_code)

    try:
        return resp.json()
    except ValueError as exc:
        raise errors.upstream(api, "respuesta no es JSON válido") from exc


async def get_json(url: str, *, api: str, params: dict | None = None, **kwargs: Any) -> Any:
    return await request_json("GET", url, api=api, params=params, **kwargs)
