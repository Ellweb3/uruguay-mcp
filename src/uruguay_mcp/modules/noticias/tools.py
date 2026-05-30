"""Discoverable tools for government news (noticias) on gub.uy.

Everything here is HTML-derived: gub.uy has no RSS/Atom/JSON feed. The listing
cards carry enough structure (title/date/url/summary/category) that we never
fetch article bodies. The sitewide search is a Google-CSE-style results page
spanning all government sites, so ``noticias_buscar`` post-filters to news URLs
and is marked ``status='partial'``.
"""

from __future__ import annotations

import html
import re
from typing import Any

from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import (
    API_NAME,
    BASE_URL,
    CARDS_PER_PAGE,
    DEFAULT_LIMIT,
    DEFAULT_SEARCH_LIMIT,
    DEFAULT_SUBSITE,
    MAX_PAGES,
    MODULE,
    NEWS_URL_MARKER,
)
from .schemas import BuscarArgs, RecientesArgs

# --- Listing card parsing -------------------------------------------------

# Each news card is wrapped in an <article about="/.../noticias/<slug>"> tag.
_CARD_RE = re.compile(
    r'<article\b[^>]*\babout="(?P<about>[^"]+)"[^>]*>(?P<body>.*?)</article>',
    re.IGNORECASE | re.DOTALL,
)
# Title link: handles both Box-title and Media-title layouts.
_TITLE_RE = re.compile(
    r'class="(?:Box-title|Media-title)"[^>]*>\s*<a\b[^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
# Category: Box-subtitle (<div><div>CAT</div></div>) or Media-subtitle (<span>CAT).
_CATEGORY_RE = re.compile(
    r'class="(?:Box-subtitle|Media-subtitle)"[^>]*>(?P<cat>.*?)</(?:div|span)>',
    re.IGNORECASE | re.DOTALL,
)
# Date lives in a Box-info element on both layouts.
_DATE_RE = re.compile(
    r'class="Box-info"[^>]*>(?P<date>.*?)</(?:div|span)>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")

# Spanish month names → month number. Uruguay commonly uses "Setiembre".
_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "setiembre": 9,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}
# "29 de Mayo, 2026"
_DATE_ES_RE = re.compile(r"(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)[,\s]+(\d{4})")
# "29/05/2026"
_DATE_NUM_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def _clean_text(raw: str) -> str:
    """Strip tags, collapse whitespace and unescape HTML entities."""
    text = _TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_date(raw: str | None) -> str | None:
    """Normalize 'DD de Month, YYYY' or 'DD/MM/YYYY' to ISO 'YYYY-MM-DD'."""
    if not raw:
        return None
    text = _clean_text(raw)
    m = _DATE_NUM_RE.search(text)
    if m:
        day, month, year = (int(g) for g in m.groups())
        return f"{year:04d}-{month:02d}-{day:02d}"
    m = _DATE_ES_RE.search(text)
    if m:
        day = int(m.group(1))
        month = _MONTHS.get(m.group(2).lower())
        year = int(m.group(3))
        if month:
            return f"{year:04d}-{month:02d}-{day:02d}"
    return text or None


def _absolute(url: str) -> str:
    """Join a relative gub.uy URL to the absolute base; pass through absolutes."""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"{BASE_URL}{url}" if url.startswith("/") else f"{BASE_URL}/{url}"


def _extract_summary(body: str) -> str | None:
    """Best-effort summary: the longest free-text block in the card body."""
    # Remove title/category/date markup so their text doesn't win as "longest".
    stripped = _TITLE_RE.sub(" ", body)
    stripped = _CATEGORY_RE.sub(" ", stripped)
    stripped = _DATE_RE.sub(" ", stripped)
    candidates = [
        _clean_text(chunk) for chunk in re.split(r"</?(?:div|p)\b[^>]*>", stripped)
    ]
    candidates = [c for c in candidates if len(c) >= 30]
    return max(candidates, key=len) if candidates else None


def _parse_listing(html_text: str) -> list[dict[str, Any]]:
    """Parse listing HTML into news cards, handling both card layouts."""
    cards: list[dict[str, Any]] = []
    for card in _CARD_RE.finditer(html_text):
        about = card.group("about")
        if NEWS_URL_MARKER not in about:
            continue
        body = card.group("body")
        title_m = _TITLE_RE.search(body)
        cat_m = _CATEGORY_RE.search(body)
        date_m = _DATE_RE.search(body)
        cards.append(
            {
                "titulo": _clean_text(title_m.group("title")) if title_m else None,
                "categoria": _clean_text(cat_m.group("cat")) if cat_m else None,
                "fecha": _normalize_date(date_m.group("date")) if date_m else None,
                "url": _absolute(about),
                "resumen": _extract_summary(body),
            }
        )
    return cards


# --- Search results parsing ----------------------------------------------

_RESULT_RE = re.compile(
    r'<li\b[^>]*class="[^"]*Results-item[^"]*"[^>]*>(?P<body>.*?)</li>',
    re.IGNORECASE | re.DOTALL,
)
_RESULT_LINK_RE = re.compile(
    r'class="Results-title"[^>]*>\s*<a\b[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_RESULT_SUMMARY_RE = re.compile(
    r'class="Results-summary"[^>]*>(?P<sum>.*?)</p>',
    re.IGNORECASE | re.DOTALL,
)


def _parse_search(html_text: str) -> list[dict[str, Any]]:
    """Parse Results-item blocks; keep only news article URLs."""
    results: list[dict[str, Any]] = []
    for item in _RESULT_RE.finditer(html_text):
        body = item.group("body")
        link_m = _RESULT_LINK_RE.search(body)
        if not link_m:
            continue
        href = html.unescape(link_m.group("href"))
        if NEWS_URL_MARKER not in href:
            continue
        sum_m = _RESULT_SUMMARY_RE.search(body)
        results.append(
            {
                "titulo": _clean_text(link_m.group("title")),
                "url": _absolute(href),
                "resumen": _clean_text(sum_m.group("sum")) if sum_m else None,
            }
        )
    return results


# --- Tools ----------------------------------------------------------------


@tool(
    name="noticias_recientes",
    module=MODULE,
    summary=(
        "Listar las noticias de gobierno más recientes desde una página de "
        "gub.uy (/{subsite}/comunicacion/noticias): título, categoría, fecha, "
        "URL y resumen, sin descargar el cuerpo de cada artículo. gub.uy no "
        "expone RSS/JSON, por lo que estos datos se extraen del HTML del listado."
    ),
    params_model=RecientesArgs,
    keywords=[
        "noticias",
        "gobierno",
        "gub.uy",
        "news",
        "government",
        "presidencia",
        "recientes",
        "latest",
    ],
)
async def noticias_recientes(
    subsite: str = DEFAULT_SUBSITE,
    limit: int = DEFAULT_LIMIT,
    pagina: int = 0,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    last_url = ""
    all_cached = True
    page = pagina
    pages_fetched = 0
    # Loop pages (~10 cards each) until we fill the limit or run out / hit cap.
    while len(items) < limit and pages_fetched < MAX_PAGES:
        html_text, cached, last_url = await client.fetch_listing(subsite, page)
        all_cached = all_cached and cached
        page_items = _parse_listing(html_text)
        items.extend(page_items)
        pages_fetched += 1
        if len(page_items) < CARDS_PER_PAGE:
            break  # last page reached
        page += 1
    items = items[:limit]
    return envelope(
        {
            "count": len(items),
            "subsite": subsite,
            "results": items,
            "nota": (
                "gub.uy no publica RSS/Atom/JSON; estas noticias se extraen del "
                "HTML del listado (título, categoría, fecha, URL y resumen de "
                "cada tarjeta, sin descargar el artículo completo)."
            ),
        },
        api=API_NAME,
        url=last_url,
        cached=all_cached if items else False,
    )


@tool(
    name="noticias_buscar",
    module=MODULE,
    summary=(
        "Buscar noticias de gobierno por texto usando el buscador de gub.uy "
        "(Drupal Search API, /buscar?search_api_fulltext=...), filtrando a "
        "resultados cuya URL contiene '/comunicacion/noticias/'. Devuelve "
        "título, URL y un resumen del buscador (no el texto del artículo). "
        "status='partial': los resultados pueden abarcar varios subsitios y los "
        "resúmenes son fragmentos del buscador, sin fecha ni categoría."
    ),
    params_model=BuscarArgs,
    keywords=[
        "noticias",
        "buscar",
        "search",
        "gub.uy",
        "gobierno",
        "news",
        "fulltext",
        "query",
    ],
)
async def noticias_buscar(
    query: str,
    limit: int = DEFAULT_SEARCH_LIMIT,
    subsite: str | None = None,
) -> dict[str, Any]:
    html_text, cached, url = await client.fetch_search(query, subsite)
    results = _parse_search(html_text)[:limit]
    return envelope(
        {
            "status": "partial",
            "query": query,
            "count": len(results),
            "results": results,
            "nota": (
                "Resultados del buscador de gub.uy filtrados a URLs de noticias. "
                "Los resúmenes son fragmentos del motor de búsqueda (no el texto "
                "del artículo) y no incluyen fecha ni categoría estructuradas; "
                "pueden provenir de distintos subsitios de gobierno."
            ),
        },
        api=API_NAME,
        url=url,
        cached=cached,
    )
