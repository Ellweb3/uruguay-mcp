"""Cliente async para las tres superficies de INUMET.

- EMA: JSON real (``.mch``) que devuelve ``application/json`` pese a la
  extensión; se pide con ``Accept: application/json`` vía ``http.get_json``.
- Pronóstico y alertas: páginas HTML de Drupal (no hay API JSON); se descarga
  el texto crudo con el cliente httpx compartido y luego se parsea.

Todo se cachea con ``cache.get_or_set`` (el JSON del EMA tiene max-age=300).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import httpx

from ...shared import cache, errors, http
from ...shared.rate_limiter import bucket_for
from .constants import ALERTA_URL, API_NAME, EMA_URL, PRONOSTICO_URL

_JSON_HEADERS = {"Accept": "application/json"}


async def fetch_ema() -> tuple[Any, bool, str]:
    """Devolver ``(payload, cached, url)`` con el JSON de estaciones (EMA)."""
    url = EMA_URL
    key = "inumet:ema"

    async def producer() -> Any:
        payload = await http.get_json(url, api=API_NAME, headers=_JSON_HEADERS)
        if not isinstance(payload, dict):
            raise errors.upstream(API_NAME, "respuesta inesperada del endpoint EMA")
        return payload

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


async def _fetch_html(url: str, key: str) -> tuple[str, bool, str]:
    """Descargar ``url`` y devolver ``(html, cached, url)`` (página Drupal)."""

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


async def fetch_pronostico() -> tuple[str, bool, str]:
    """Devolver ``(html, cached, url)`` de la página de pronóstico."""
    return await _fetch_html(PRONOSTICO_URL, "inumet:pronostico")


async def fetch_alerta() -> tuple[str, bool, str]:
    """Devolver ``(html, cached, url)`` de la página de alertas/advertencias."""
    return await _fetch_html(ALERTA_URL, "inumet:alerta")
