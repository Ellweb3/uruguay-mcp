"""Discoverable tools for the State APIs/services catalog (gub.uy showcases)."""

from __future__ import annotations

from typing import Any

from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import API_NAME, API_RES_FORMAT, MODULE
from .schemas import (
    GetServicioArgs,
    ListServiciosArgs,
    SearchApisArgs,
    ServicioDatasetsArgs,
)


def _slim_showcase(sc: dict[str, Any]) -> dict[str, Any]:
    """Project a showcase down to the fields a model actually needs.

    Drops the HTML ``showcase_notes_formatted`` and keeps plain ``notes``.
    """
    return {
        "id": sc.get("id"),
        "name": sc.get("name"),
        "title": sc.get("title"),
        "notes": sc.get("notes"),
        "url": sc.get("url"),
        "author": sc.get("author"),
        "tags": [t.get("name") for t in sc.get("tags", [])],
        "image_url": sc.get("image_display_url") or sc.get("image_url"),
        "num_datasets": sc.get("num_datasets"),
        "metadata_modified": sc.get("metadata_modified"),
    }


def _slim_dataset(pkg: dict[str, Any]) -> dict[str, Any]:
    """Project a CKAN package down to the fields a model actually needs."""
    return {
        "id": pkg.get("id"),
        "name": pkg.get("name"),
        "title": pkg.get("title"),
        "notes": pkg.get("notes"),
        "organization": (pkg.get("organization") or {}).get("title"),
        "tags": [t.get("name") for t in pkg.get("tags", [])],
        "num_resources": pkg.get("num_resources"),
        "metadata_modified": pkg.get("metadata_modified"),
        "resources": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "format": r.get("format"),
                "url": r.get("url"),
            }
            for r in pkg.get("resources", [])
        ],
    }


def _matches(sc: dict[str, Any], query: str, tag: str | None) -> bool:
    if tag:
        names = {t.get("name") for t in sc.get("tags", [])}
        if tag not in names:
            return False
    if query:
        q = query.lower()
        haystack = " ".join(
            str(sc.get(k) or "") for k in ("title", "notes", "name", "author")
        ).lower()
        if q not in haystack:
            return False
    return True


@tool(
    name="gubuy_list_servicios",
    module=MODULE,
    summary=(
        "Listar el catálogo de aplicaciones y servicios/APIs del Estado uruguayo "
        "(showcases de catalogodatos.gub.uy): nombre, URL en vivo, descripción y "
        "etiquetas. Filtro de texto/etiqueta aplicado del lado del cliente."
    ),
    params_model=ListServiciosArgs,
    keywords=[
        "servicios",
        "aplicaciones",
        "apis",
        "gobierno",
        "estado",
        "catalogo",
        "showcase",
        "gubuy",
        "listado",
    ],
)
async def list_servicios(
    query: str = "",
    tag: str | None = None,
    limit: int = 50,
    start: int = 0,
) -> dict[str, Any]:
    result, cached, url = await client.showcase_list()
    items = result or []
    filtered = [sc for sc in items if _matches(sc, query, tag)]
    total = len(filtered)
    page = filtered[start : start + limit]
    return envelope(
        {
            "count": total,
            "results": [_slim_showcase(sc) for sc in page],
        },
        api=API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="gubuy_get_servicio",
    module=MODULE,
    summary=(
        "Obtener el detalle de una aplicación/servicio del Estado por ID o slug: "
        "descripción, URL, etiquetas, imagen y cantidad de datasets vinculados."
    ),
    params_model=GetServicioArgs,
    keywords=["servicio", "aplicacion", "detalle", "showcase", "api", "gubuy"],
)
async def get_servicio(id: str) -> dict[str, Any]:
    result, cached, url = await client.showcase_show(id)
    return envelope(_slim_showcase(result), api=API_NAME, url=url, cached=cached)


@tool(
    name="gubuy_servicio_datasets",
    module=MODULE,
    summary=(
        "Listar los datasets del Catálogo Nacional que alimentan una "
        "aplicación/servicio del Estado (puede estar vacío si no hay vínculos)."
    ),
    params_model=ServicioDatasetsArgs,
    keywords=["servicio", "datasets", "vinculados", "fuentes", "showcase", "gubuy"],
)
async def servicio_datasets(showcase_id: str) -> dict[str, Any]:
    result, cached, url = await client.showcase_package_list(showcase_id)
    datasets = [_slim_dataset(p) for p in (result or [])]
    return envelope(
        {"count": len(datasets), "results": datasets},
        api=API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="gubuy_search_apis",
    module=MODULE,
    summary=(
        "Buscar datasets del Estado que exponen recursos consumibles por API/JSON "
        "(res_format:JSON), con búsqueda de texto y paginación."
    ),
    params_model=SearchApisArgs,
    keywords=[
        "api",
        "json",
        "datos",
        "servicio web",
        "consumir",
        "integracion",
        "gubuy",
        "buscar",
    ],
)
async def search_apis(query: str = "", rows: int = 20, start: int = 0) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": query or "*:*",
        "fq": f"res_format:{API_RES_FORMAT}",
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
