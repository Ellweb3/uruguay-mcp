"""Discoverable tools for the INE statistical catalog (ANDA/NADA + CKAN)."""

from __future__ import annotations

from typing import Any

from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import API_NAME, CKAN_API_NAME, CKAN_ORG_SLUG, MODULE
from .schemas import (
    DatasetResourcesArgs,
    DatastoreFieldsArgs,
    DatastoreQueryArgs,
    FindDataResourcesArgs,
    GetStudyArgs,
    ListCkanDatasetsArgs,
    SearchStudiesArgs,
)


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


def _slim_resource_brief(r: dict[str, Any]) -> dict[str, Any]:
    """Project a CKAN resource down to the fields needed to query it."""
    return {
        "id": r.get("id"),
        "name": r.get("name"),
        "format": r.get("format"),
        "datastore_active": bool(r.get("datastore_active")),
        "url": r.get("url"),
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


@tool(
    name="ine_find_data_resources",
    module=MODULE,
    summary=(
        "Descubrir recursos CONSULTABLES del INE: busca datasets (organization=ine) "
        "en el Catálogo Nacional y devuelve SOLO los recursos con DataStore activo "
        "(id, nombre, formato, dataset). Los ids hallados se usan luego con "
        "ine_datastore_query."
    ),
    params_model=FindDataResourcesArgs,
    keywords=[
        "ine",
        "ckan",
        "datastore",
        "recursos",
        "consultable",
        "series",
        "tabular",
        "descubrir",
        "find",
        "resources",
    ],
)
async def find_data_resources(
    theme: str = "",
    rows: int = 20,
    start: int = 0,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": theme or "*:*",
        "fq": f"organization:{CKAN_ORG_SLUG}",
        "rows": rows,
        "start": start,
    }
    result, cached, url = await client.ckan_package_search(params)
    datasets: list[dict[str, Any]] = []
    total_active = 0
    for pkg in result.get("results", []):
        active = [
            _slim_resource_brief(r)
            for r in pkg.get("resources", [])
            if r.get("datastore_active")
        ]
        if not active:
            continue
        total_active += len(active)
        datasets.append(
            {
                "dataset_name": pkg.get("name"),
                "dataset_title": pkg.get("title"),
                "resources": active,
            }
        )
    return envelope(
        {
            "count": result.get("count"),
            "datasets_with_data": len(datasets),
            "active_resources": total_active,
            "results": datasets,
        },
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="ine_datastore_query",
    module=MODULE,
    summary=(
        "Consultar filas de un recurso del INE con DataStore activo "
        "(datastore_search). Devuelve el esquema de columnas (fields), el total y "
        "las filas (records). Primero obtené el resource_id con "
        "ine_find_data_resources."
    ),
    params_model=DatastoreQueryArgs,
    keywords=[
        "ine",
        "ckan",
        "datastore",
        "consultar",
        "filas",
        "registros",
        "query",
        "records",
        "tabla",
        "datos",
    ],
)
async def datastore_query(
    resource_id: str,
    limit: int = 20,
    offset: int = 0,
    q: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "resource_id": resource_id,
        "limit": limit,
        "offset": offset,
    }
    if q:
        params["q"] = q
    result, cached, url = await client.ckan_datastore_search(params)
    fields = [
        {"id": f.get("id"), "type": f.get("type")}
        for f in result.get("fields", [])
    ]
    return envelope(
        {
            "resource_id": result.get("resource_id", resource_id),
            "fields": fields,
            "total": result.get("total"),
            "limit": limit,
            "offset": offset,
            "records": result.get("records", []),
        },
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="ine_datastore_fields",
    module=MODULE,
    summary=(
        "Obtener SOLO el esquema de columnas (id y tipo) de un recurso del INE con "
        "DataStore activo, sin traer filas (limit=0). Útil para armar filtros antes "
        "de consultar con ine_datastore_query."
    ),
    params_model=DatastoreFieldsArgs,
    keywords=[
        "ine",
        "ckan",
        "datastore",
        "columnas",
        "esquema",
        "campos",
        "fields",
        "schema",
        "tipos",
    ],
)
async def datastore_fields(resource_id: str) -> dict[str, Any]:
    params: dict[str, Any] = {"resource_id": resource_id, "limit": 0}
    result, cached, url = await client.ckan_datastore_search(params)
    fields = [
        {"id": f.get("id"), "type": f.get("type")}
        for f in result.get("fields", [])
    ]
    return envelope(
        {
            "resource_id": result.get("resource_id", resource_id),
            "total": result.get("total"),
            "fields": fields,
        },
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="ine_dataset_resources",
    module=MODULE,
    summary=(
        "Detalle de un dataset del INE en el Catálogo Nacional (package_show): "
        "lista todos sus recursos indicando cuáles tienen DataStore activo "
        "(consultables con ine_datastore_query) y cuáles solo se descargan."
    ),
    params_model=DatasetResourcesArgs,
    keywords=[
        "ine",
        "ckan",
        "dataset",
        "recursos",
        "detalle",
        "package",
        "resources",
        "descarga",
    ],
)
async def dataset_resources(dataset_name: str) -> dict[str, Any]:
    result, cached, url = await client.ckan_package_show(dataset_name)
    resources = [_slim_resource_brief(r) for r in result.get("resources", [])]
    return envelope(
        {
            "id": result.get("id"),
            "name": result.get("name"),
            "title": result.get("title"),
            "notes": result.get("notes"),
            "organization": (result.get("organization") or {}).get("title"),
            "num_resources": result.get("num_resources"),
            "queryable_resources": [r["id"] for r in resources if r["datastore_active"]],
            "resources": resources,
        },
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )
