"""Async client over IMPO's ``?json=true`` open-data mechanism.

IMPO no expone una API JSON convencional: para cada URL de norma se agrega
``?json=true`` y el servidor responde un JSON codificado en latin-1
(``charset=ISO-8859-1``). Hay que decodificar los bytes como ISO-8859-1 antes
de ``json.loads`` o los acentos se rompen (``Art�culo``). Por eso este cliente
NO usa ``http.get_json`` (que asume utf-8) sino que pide la respuesta cruda y
la decodifica a mano.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote_plus

import httpx

from ...shared import cache, errors, http
from .constants import API_NAME, BASE_URL, ENCODING, NEWS_FEED_URL, SEARCH_FEED_URL


async def _get_json_latin1(url: str, key: str) -> tuple[Any, bool, str]:
    """GET ``url`` (con ?json=true ya incluido), decodificar latin-1 (cacheado)."""

    async def producer() -> Any:
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
        try:
            text = resp.content.decode(ENCODING)
        except UnicodeDecodeError as exc:
            raise errors.upstream(API_NAME, "no se pudo decodificar (ISO-8859-1)") from exc
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            # Norma inexistente o slug no soportado devuelve HTML, no JSON.
            raise errors.upstream(
                API_NAME, "la respuesta no es JSON (¿norma inexistente o slug inválido?)"
            ) from exc

    value, cached_flag = await cache.get_or_set(key, producer)
    return value, cached_flag, url


async def get_norma(slug: str, ruta: str) -> tuple[Any, bool, str]:
    """Obtener una norma consolidada/original como JSON.

    ``slug`` es la base (ej. 'leyes', 'decretos-originales', 'constitucion').
    ``ruta`` es el identificador de la norma (ej. '18331-2008', '1967-1967').
    """
    url = f"{BASE_URL}/bases/{slug}/{ruta}?json=true"
    key = f"impo:norma:{slug}:{ruta}"
    return await _get_json_latin1(url, key)


async def _fetch_feed(url: str, key: str) -> tuple[str, bool, str]:
    """GET un feed RSS de WordPress (UTF-8) como texto crudo (cacheado).

    Los feeds (/?s=...&feed=rss2 y /feed/) son UTF-8, a diferencia de las bases
    ?json=true (latin-1). Se devuelve el texto para parsearlo con ElementTree.
    """

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


async def fetch_search_feed(query: str, paged: int) -> tuple[str, bool, str]:
    """Feed RSS de la búsqueda full-text del sitio (/?s=...&feed=rss2&paged=N)."""
    url = SEARCH_FEED_URL.format(query=quote_plus(query), paged=paged)
    key = f"impo:search:{query}:{paged}"
    return await _fetch_feed(url, key)


async def fetch_news_feed() -> tuple[str, bool, str]:
    """Feed RSS de novedades/noticias editoriales del sitio (/feed/)."""
    return await _fetch_feed(NEWS_FEED_URL, "impo:feed")
