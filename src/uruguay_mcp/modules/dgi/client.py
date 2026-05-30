"""Async client that fetches raw DGI surfaces from gub.uy (HTML + binarios).

La DGI no expone una API: los listados son HTML (de los que se extraen los
enlaces a archivos) y los datos son binarios ``.ods``/``.xlsx``/``.csv`` o
boletines ``.pdf``. Por eso este cliente NO usa ``http.get_json`` sino que pide
la respuesta cruda (``resp.text`` para el HTML, ``resp.content`` para los
binarios), mirroring el patrón de ine/client.py e impo/client.py. Cada fetch se
cachea por URL y se limita por host (www.gub.uy).
"""

from __future__ import annotations

from urllib.parse import urlencode

import httpx

from ...shared import cache, errors, http
from .constants import (
    API_NAME,
    BASE_URL,
    BOLETIN_PATH,
    DATOS_PATH,
    GASTO_PATH,
)


async def _fetch_text(url: str, key: str) -> tuple[str, bool, str]:
    """GET ``url`` y devolver su HTML como texto crudo (cacheado)."""

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


async def _fetch_bytes(url: str, key: str) -> tuple[bytes, bool, str]:
    """GET ``url`` y devolver el contenido binario crudo (.ods/.xlsx/.csv/.pdf)."""

    async def producer() -> bytes:
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
        return resp.content

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


async def fetch_datos_page(page: int) -> tuple[str, bool, str]:
    """HTML del listado de archivos de valores de referencia (?page=N, 0-based)."""
    url = f"{BASE_URL}{DATOS_PATH}"
    if page:
        url = f"{url}?{urlencode({'page': page})}"
    return await _fetch_text(url, f"dgi:datos:{page}")


async def fetch_boletines() -> tuple[str, bool, str]:
    """HTML de la página de boletines estadísticos (enlaces a PDFs)."""
    url = f"{BASE_URL}{BOLETIN_PATH}"
    return await _fetch_text(url, "dgi:boletines")


async def fetch_gasto_tributario() -> tuple[str, bool, str]:
    """HTML de la página de gasto tributario (enlaces a PDFs)."""
    url = f"{BASE_URL}{GASTO_PATH}"
    return await _fetch_text(url, "dgi:gasto")


async def fetch_archivo(url: str) -> tuple[bytes, bool, str]:
    """Descargar un archivo de datos (.ods/.xlsx/.csv) como bytes (cacheado)."""
    return await _fetch_bytes(url, f"dgi:archivo:{url}")
