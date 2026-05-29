"""Discoverable tools for the INE statistical catalog (ANDA/NADA + CKAN)."""

from __future__ import annotations

from typing import Any

from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import API_NAME, CKAN_API_NAME, CKAN_ORG_SLUG, MODULE
from .schemas import GetStudyArgs, ListCkanDatasetsArgs, SearchStudiesArgs


def _slim_search_row(row: dict[str, Any]) -> dict[str, Any]:
    """Project an ANDA search row down to the fields a model needs.

    Surfaces ``idno`` (the URY-...-vNN string) prominently, since study-detail
    lookups require it — the numeric ``id`` is NOT accepted by catalog/{idno}.
    """
    return {
        "idno": row.get("idno"),
        "id": row.get("id"),
        "title": row.get("title"),
        "nation": row.get("nation"),
        "authoring_entity": row.get("authoring_entity"),
        "form_model": row.get("form_model"),
        "year_start": row.get("year_start"),
        "year_end": row.get("year_end"),
        "repo_title": row.get("repo_title"),
        "total_views": row.get("total_views"),
        "total_downloads": row.get("total_downloads"),
        "url": row.get("url"),
    }


def _slim_study(ds: dict[str, Any]) -> dict[str, Any]:
    """Project an ANDA study detail down to the fields a model needs."""
    return {
        "idno": ds.get("idno"),
        "id": ds.get("id"),
        "type": ds.get("type"),
        "title": ds.get("title"),
        "nation": ds.get("nation"),
        "authoring_entity": ds.get("authoring_entity"),
        "year_start": ds.get("year_start"),
        "year_end": ds.get("year_end"),
        "varcount": ds.get("varcount"),
        "published": ds.get("published"),
        "created": ds.get("created"),
        "changed": ds.get("changed"),
        "data_access_type": ds.get("data_access_type"),
        "remote_data_url": ds.get("remote_data_url"),
        "link_study": ds.get("link_study"),
        "link_questionnaire": ds.get("link_questionnaire"),
        "link_indicator": ds.get("link_indicator"),
        "link_technical": ds.get("link_technical"),
        "link_report": ds.get("link_report"),
        "total_views": ds.get("total_views"),
        "total_downloads": ds.get("total_downloads"),
        "metadata": ds.get("metadata"),
    }


def _slim_ckan_dataset(pkg: dict[str, Any]) -> dict[str, Any]:
    """Project a CKAN package down to the fields a model needs."""
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
            }
            for r in pkg.get("resources", [])
        ],
    }


@tool(
    name="ine_search_studies",
    module=MODULE,
    summary=(
        "Buscar estudios/operaciones estadísticas en el catálogo ANDA alojado por "
        "el INE (software NADA). Devuelve estudios con su idno, título, organismo "
        "responsable, años y enlaces."
    ),
    params_model=SearchStudiesArgs,
    keywords=[
        "ine",
        "anda",
        "nada",
        "estadistica",
        "microdatos",
        "estudio",
        "encuesta",
        "censo",
        "buscar",
        "catalogo",
        "search",
        "survey",
    ],
)
async def search_studies(
    query: str = "",
    rows: int = 20,
    page: int = 1,
    year_from: int | None = None,
    year_to: int | None = None,
    sort_by: str | None = None,
    sort_order: str = "desc",
) -> dict[str, Any]:
    params: dict[str, Any] = {"ps": rows, "page": page, "sort_order": sort_order}
    if query:
        params["sk"] = query
    if year_from is not None:
        params["from"] = year_from
    if year_to is not None:
        params["to"] = year_to
    if sort_by:
        params["sort_by"] = sort_by
    result, cached, url = await client.search_studies(params)
    rows_data = result.get("rows") or []
    return envelope(
        {
            "found": result.get("found"),
            "total": result.get("total"),
            "limit": result.get("limit"),
            "offset": result.get("offset"),
            "results": [_slim_search_row(r) for r in rows_data],
        },
        api=API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="ine_get_study",
    module=MODULE,
    summary=(
        "Obtener metadatos completos de un estudio por su idno ANDA "
        "(p.ej. 'URY-INE-...-vNN'): descripción, acceso a datos, cuestionario, "
        "informes técnicos y enlaces de descarga."
    ),
    params_model=GetStudyArgs,
    keywords=[
        "ine",
        "anda",
        "nada",
        "estudio",
        "metadatos",
        "detalle",
        "microdatos",
        "ddi",
        "study",
        "metadata",
        "idno",
    ],
)
async def get_study(idno: str) -> dict[str, Any]:
    result, cached, url = await client.get_study(idno)
    return envelope(_slim_study(result), api=API_NAME, url=url, cached=cached)


@tool(
    name="ine_list_ckan_datasets",
    module=MODULE,
    summary=(
        "Fallback: listar datasets del INE publicados en el Catálogo Nacional "
        "(CKAN, organization=ine). Útil para recursos tabulares/descargables que "
        "no están en ANDA."
    ),
    params_model=ListCkanDatasetsArgs,
    keywords=[
        "ine",
        "ckan",
        "catalogodatos",
        "datos abiertos",
        "fallback",
        "organizacion",
        "dataset",
    ],
)
async def list_ckan_datasets(
    query: str = "",
    rows: int = 20,
    start: int = 0,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": query or "*:*",
        "fq": f"organization:{CKAN_ORG_SLUG}",
        "rows": rows,
        "start": start,
    }
    result, cached, url = await client.ckan_package_search(params)
    return envelope(
        {
            "count": result.get("count"),
            "results": [_slim_ckan_dataset(p) for p in result.get("results", [])],
        },
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )
