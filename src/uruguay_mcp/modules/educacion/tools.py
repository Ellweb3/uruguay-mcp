"""Discoverable tools for ANEP educational open data (via CKAN)."""

from __future__ import annotations

import json
from typing import Any

from ...shared import errors
from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import (
    API_NAME,
    DATASET_OFERTA,
    DATASTORE_RESOURCES,
    DEFAULT_RESOURCE,
    MODULE,
    ORG,
)
from .schemas import BuscarArgs, CentrosArgs, DatasetArgs

# Subsistemas known to be download-only (no active datastore). For these we
# resolve the resource URL from package_show instead of querying a datastore.
_DOWNLOAD_ONLY = {"ceip", "cetp"}


def _slim_dataset(pkg: dict[str, Any]) -> dict[str, Any]:
    """Project a CKAN package down to the fields a model actually needs."""
    return {
        "id": pkg.get("id"),
        "name": pkg.get("name"),
        "title": pkg.get("title"),
        "notes": pkg.get("notes"),
        "organization": (pkg.get("organization") or {}).get("title"),
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


@tool(
    name="educacion_buscar",
    module=MODULE,
    summary=(
        "Buscar datasets educativos de ANEP en el Catálogo Nacional (CKAN), "
        "con fq=organization:anep fijado para no mezclar otras organizaciones."
    ),
    params_model=BuscarArgs,
    keywords=[
        "anep",
        "educacion",
        "buscar",
        "search",
        "datasets",
        "ckan",
        "educacion publica",
    ],
)
async def educacion_buscar(q: str = "", rows: int = 20, start: int = 0) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": q or "*:*",
        "fq": f"organization:{ORG}",
        "rows": rows,
        "start": start,
    }
    result, cached, url = await client.package_search(params)
    return envelope(
        {
            "count": result.get("count"),
            "results": [_slim_dataset(p) for p in result.get("results", [])],
        },
        api=API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="educacion_get_dataset",
    module=MODULE,
    summary=(
        "Obtener un dataset de ANEP por slug/UUID (package_show), con sus "
        "recursos: id, formato, url y datastore_active (consultable o solo "
        "descarga)."
    ),
    params_model=DatasetArgs,
    keywords=[
        "anep",
        "educacion",
        "dataset",
        "package",
        "show",
        "resources",
        "metadata",
    ],
)
async def educacion_get_dataset(id: str) -> dict[str, Any]:
    result, cached, url = await client.package_show(id)
    return envelope(_slim_dataset(result), api=API_NAME, url=url, cached=cached)


def _resolve_download_url(pkg: dict[str, Any], subsistema: str | None) -> dict[str, Any] | None:
    """Find a matching resource URL in the 'Oferta educativa' dataset.

    Matches by the subsistema token (ceip/cetp/ces/cfe) appearing in the
    resource name. Returns a slim resource dict, or None if not found.
    """
    token = (subsistema or "").lower()
    for r in pkg.get("resources", []):
        name = str(r.get("name", "")).lower()
        if token and token in name:
            return {
                "id": r.get("id"),
                "name": r.get("name"),
                "format": r.get("format"),
                "url": r.get("url"),
                "datastore_active": r.get("datastore_active", False),
            }
    return None


@tool(
    name="educacion_centros",
    module=MODULE,
    summary=(
        "Consultar centros educativos de ANEP. Si el recurso elegido tiene "
        "datastore activo (por defecto Secundaria/DGES) ejecuta datastore_search "
        "con q + filtros departamento/localidad; si no (Primaria/UTU), devuelve "
        "la URL de descarga del recurso en vez de fallar."
    ),
    params_model=CentrosArgs,
    keywords=[
        "anep",
        "centros",
        "educativos",
        "escuelas",
        "liceos",
        "schools",
        "centers",
        "datastore",
        "departamento",
        "matricula",
    ],
)
async def educacion_centros(
    q: str | None = None,
    departamento: str | None = None,
    localidad: str | None = None,
    subsistema: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    sub = (subsistema or "").lower() or None

    # Download-only subsistemas: surface the resource URL from package_show.
    if sub in _DOWNLOAD_ONLY:
        pkg, cached, url = await client.package_show(DATASET_OFERTA)
        resource = _resolve_download_url(pkg, sub)
        return envelope(
            {
                "mode": "download",
                "subsistema": sub,
                "message": (
                    "Este subsistema no tiene datastore consultable; usá la URL "
                    "del recurso para descargar el XLSX."
                ),
                "resource": resource,
            },
            api=API_NAME,
            url=url,
            cached=cached,
        )

    # Datastore-backed subsistemas (default = Secundaria/DGES).
    resource_id = DATASTORE_RESOURCES.get(sub, DEFAULT_RESOURCE) if sub else DEFAULT_RESOURCE
    params: dict[str, Any] = {"resource_id": resource_id, "limit": limit, "offset": offset}
    if q:
        params["q"] = q
    filters: dict[str, str] = {}
    if departamento:
        filters["Departamento"] = departamento
    if localidad:
        filters["Localidad"] = localidad
    if filters:
        params["filters"] = json.dumps(filters, ensure_ascii=False)

    try:
        result, cached, url = await client.datastore_search(params)
    except errors.NotFoundError:
        # Resource lost its datastore: degrade to the download URL.
        pkg, cached, url = await client.package_show(DATASET_OFERTA)
        resource = next(
            (
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "format": r.get("format"),
                    "url": r.get("url"),
                    "datastore_active": r.get("datastore_active", False),
                }
                for r in pkg.get("resources", [])
                if r.get("id") == resource_id
            ),
            None,
        )
        return envelope(
            {
                "mode": "download",
                "subsistema": sub,
                "message": "El recurso no tiene datastore activo; usá la URL de descarga.",
                "resource": resource,
            },
            api=API_NAME,
            url=url,
            cached=cached,
        )

    return envelope(
        {
            "mode": "datastore",
            "subsistema": sub or "ces",
            "resource_id": resource_id,
            "total": result.get("total"),
            "fields": result.get("fields"),
            "records": result.get("records"),
        },
        api=API_NAME,
        url=url,
        cached=cached,
    )
