"""Discoverable tools for MIDES (Ministerio de Desarrollo Social).

Two surfaces: CKAN open data (datasets + datastore series) and the Guía
Nacional de Recursos Sociales (HTML-scraped social-program directory).
"""

from __future__ import annotations

import re
from typing import Any

from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import (
    CKAN_API_NAME,
    CKAN_ORG,
    GUIA_API_NAME,
    GUIA_BASE_URL,
    MODULE,
)
from .schemas import BuscarArgs, DatasetArgs, RecursosArgs, SerieArgs

# Canonical Guía resource links look like https://.../{id}/{slug} (slug lowercase).
_RECURSO_RE = re.compile(
    r"https://guiaderecursos\.mides\.gub\.uy/(\d+)/([a-z0-9-]+)"
)
# Strip HTML tags when deriving a readable title from anchor inner text.
_TAG_RE = re.compile(r"<[^>]+>")


def _slim_dataset(pkg: dict[str, Any]) -> dict[str, Any]:
    """Project a CKAN package down to the fields a model actually needs."""
    return {
        "id": pkg.get("id"),
        "name": pkg.get("name"),
        "title": pkg.get("title"),
        "notes": pkg.get("notes"),
        "organization": (pkg.get("organization") or {}).get("title"),
        "groups": [g.get("title") for g in pkg.get("groups", [])],
        "tags": [t.get("name") for t in pkg.get("tags", [])],
        "num_resources": pkg.get("num_resources"),
        "metadata_modified": pkg.get("metadata_modified"),
        "resources": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "format": r.get("format"),
                "url": r.get("url"),
                "datastore_active": r.get("datastore_active", False),
            }
            for r in pkg.get("resources", [])
        ],
    }


def _parse_recursos(html: str, limit: int) -> list[dict[str, Any]]:
    """Scrape canonical Guía resource links and a nearby title from the HTML.

    Defensive by design: matches the stable canonical-URL pattern and derives a
    human title from the anchor inner text when present. Deduplicates by id.
    """
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for m in _RECURSO_RE.finditer(html):
        rid, slug = m.group(1), m.group(2)
        if rid in seen:
            continue
        seen.add(rid)
        url = f"{GUIA_BASE_URL}/{rid}/{slug}"
        # Best-effort: grab the anchor's inner text right after this href.
        title = slug.replace("-", " ").strip().capitalize()
        tail = html[m.end() : m.end() + 400]
        anchor = re.search(r"['\"]?\s*>(.*?)</a>", tail, re.DOTALL)
        if anchor:
            text = _TAG_RE.sub("", anchor.group(1)).strip()
            if text:
                title = text
        out.append({"id": rid, "slug": slug, "title": title, "url": url})
        if len(out) >= limit:
            break
    return out


@tool(
    name="mides_buscar",
    module=MODULE,
    summary=(
        "Buscar datasets del MIDES en el Catálogo Nacional de Datos Abiertos "
        "(CKAN). Fuerza fq=organization:mides. Cubre prestaciones sociales "
        "(Tarjeta Uruguay Social/TUS, Asignaciones Familiares-Plan de Equidad/"
        "AFAM-PE, Asistencia a la Vejez), encuestas (ENDIS) e indicadores."
    ),
    params_model=BuscarArgs,
    keywords=[
        "mides",
        "prestaciones",
        "beneficios",
        "tarjeta uruguay social",
        "tus",
        "asignaciones familiares",
        "afam",
        "plan de equidad",
        "asistencia a la vejez",
        "beneficiarios",
        "datasets",
        "ckan",
        "datos abiertos",
        "desarrollo social",
        "buscar",
    ],
)
async def buscar(query: str = "", rows: int = 20, start: int = 0) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": query or "*:*",
        "fq": f"organization:{CKAN_ORG}",
        "rows": rows,
        "start": start,
    }
    result, cached, url = await client.package_search(params)
    return envelope(
        {
            "count": result.get("count"),
            "results": [_slim_dataset(p) for p in result.get("results", [])],
        },
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="mides_get_dataset",
    module=MODULE,
    summary=(
        "Obtener el detalle de un dataset del MIDES por id/name (CKAN "
        "package_show): notas, grupos, tags y la lista de recursos con id, "
        "formato (CSV/JSON/XLSX/XML), url de descarga y datastore_active. Es el "
        "paso previo para leer la serie temporal con mides_serie."
    ),
    params_model=DatasetArgs,
    keywords=[
        "mides",
        "dataset",
        "package_show",
        "detalle",
        "recursos",
        "indicador",
        "metadatos",
        "ckan",
        "csv",
        "datastore",
    ],
)
async def get_dataset(id: str) -> dict[str, Any]:
    result, cached, url = await client.package_show(id)
    return envelope(_slim_dataset(result), api=CKAN_API_NAME, url=url, cached=cached)


@tool(
    name="mides_serie",
    module=MODULE,
    summary=(
        "Leer los datos tabulares (serie temporal mensual) de un recurso del "
        "MIDES con datastore activo (CKAN datastore_search): ej. evolución "
        "mensual de Tarjetas Uruguay Social, beneficiarios de AFAM-PE o "
        "Asistencia a la Vejez. Devuelve fields + records con limit/offset/sort/q."
    ),
    params_model=SerieArgs,
    keywords=[
        "mides",
        "serie",
        "datos",
        "datastore",
        "evolucion mensual",
        "beneficiarios",
        "valores",
        "tus",
        "afam",
        "vejez",
        "tabular",
        "csv",
        "registros",
    ],
)
async def serie(
    resource_id: str,
    limit: int = 100,
    offset: int = 0,
    sort: str | None = None,
    q: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "resource_id": resource_id,
        "limit": limit,
        "offset": offset,
    }
    if sort:
        params["sort"] = sort
    if q:
        params["q"] = q
    result, cached, url = await client.datastore_search(params)
    return envelope(
        {
            "total": result.get("total"),
            "fields": result.get("fields"),
            "records": result.get("records"),
        },
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="mides_recursos",
    module=MODULE,
    summary=(
        "Buscar en la Guía Nacional de Recursos Sociales "
        "(guiaderecursos.mides.gub.uy) programas/servicios sociales por "
        "necesidad. La Guía no expone API JSON: la tool hace una búsqueda GET "
        "sobre el portal JSP y parsea el HTML para devolver, por cada recurso, "
        "su id, título y URL canónica. Degrada con elegancia: si la búsqueda "
        "falla, devuelve las URLs de entrada a la Guía."
    ),
    params_model=RecursosArgs,
    keywords=[
        "mides",
        "guia de recursos",
        "recursos sociales",
        "guiaderecursos",
        "programas",
        "servicios",
        "prestaciones",
        "ayuda social",
        "violencia",
        "vejez",
        "discapacidad",
        "situacion de calle",
        "donde acudir",
        "necesidad",
    ],
)
async def recursos(
    query: str,
    area: int | None = None,
    poblacion: int | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "cmdaction": "search",
        "query": query,
        "channel": "innova.front",
        "contentid": "28167",
        "site": "1",
    }
    if area is not None:
        params["area"] = area
    if poblacion is not None:
        params["poblacion"] = poblacion

    html, cached, url = await client.fetch_guia(params)
    results = _parse_recursos(html, limit)
    data: dict[str, Any] = {
        "query": query,
        "count": len(results),
        "results": results,
    }
    if not results:
        # Degrade gracefully: hand back canonical entry points to the Guía.
        data["fallback"] = {
            "message": (
                "No se pudieron extraer recursos del HTML de la Guía. "
                "Ingresá manualmente o consultá el recurso "
                "uru://mides/guia-recursos para saber cómo navegarla."
            ),
            "guia_url": GUIA_BASE_URL,
        }
    return envelope(data, api=GUIA_API_NAME, url=url, cached=cached)
