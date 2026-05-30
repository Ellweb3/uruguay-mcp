"""Discoverable tools for the national open-data catalog."""

from __future__ import annotations

import re
from typing import Any

from ...shared import errors
from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import DEFAULT_ROWS, MODULE
from .schemas import (
    DatasetArgs,
    DatastoreSearchArgs,
    DatastoreSqlArgs,
    GroupsArgs,
    OrganizationsArgs,
    RecentDatasetsArgs,
    ResourceArgs,
    SearchDatasetsArgs,
    TagsArgs,
)

# Keywords that turn a read-only SELECT into something the datastore must reject.
_FORBIDDEN_SQL = re.compile(
    r"\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|GRANT|REVOKE|TRUNCATE|COPY)\b",
    re.IGNORECASE,
)


def _guard_sql(sql: str) -> str:
    """Enforce a strict single SELECT/WITH statement before hitting the WAF.

    The portal's WAF answers 'unsafe' SQL with an HTML page that the JSON layer
    rejects as an opaque upstream error. We validate client-side first so the
    caller gets a clear, actionable validation message instead.
    """
    cleaned = sql.strip()
    if not cleaned:
        raise errors.ValidationError("La consulta SQL no puede estar vacía.")
    # Allow a single optional trailing semicolon; reject any internal one.
    body = cleaned[:-1] if cleaned.endswith(";") else cleaned
    if ";" in body:
        raise errors.ValidationError(
            "Solo se permite una única sentencia SELECT (sin ';' intermedios)."
        )
    if "--" in body or "/*" in body or "*/" in body:
        raise errors.ValidationError(
            "No se permiten comentarios SQL ('--', '/*', '*/') en la consulta."
        )
    if not re.match(r"^(SELECT|WITH)\b", body, re.IGNORECASE):
        raise errors.ValidationError(
            "La consulta debe ser de solo lectura y comenzar con SELECT (o WITH)."
        )
    if _FORBIDDEN_SQL.search(body):
        raise errors.ValidationError(
            "Solo se admiten consultas de lectura; no se permite DDL/DML "
            "(DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, etc.)."
        )
    return body


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


def _build_fq(organization: str | None, group: str | None, tags: list[str]) -> str | None:
    clauses = []
    if organization:
        clauses.append(f"organization:{organization}")
    if group:
        clauses.append(f"groups:{group}")
    clauses.extend(f"tags:{tag}" for tag in tags)
    return " ".join(clauses) or None


@tool(
    name="catalogo_search_datasets",
    module=MODULE,
    summary="Buscar datasets en el Catálogo Nacional de Datos Abiertos de Uruguay (CKAN).",
    params_model=SearchDatasetsArgs,
    keywords=["datos abiertos", "buscar", "dataset", "catalogo", "ckan", "uruguay", "search"],
)
async def search_datasets(
    query: str = "",
    organization: str | None = None,
    group: str | None = None,
    tags: list[str] | None = None,
    rows: int = 20,
    start: int = 0,
) -> dict[str, Any]:
    params: dict[str, Any] = {"q": query or "*:*", "rows": rows, "start": start}
    fq = _build_fq(organization, group, tags or [])
    if fq:
        params["fq"] = fq
    result, cached, url = await client.package_search(params)
    return envelope(
        {
            "count": result.get("count"),
            "results": [_slim_dataset(p) for p in result.get("results", [])],
        },
        api="catalogodatos.gub.uy",
        url=url,
        cached=cached,
    )


@tool(
    name="catalogo_get_dataset",
    module=MODULE,
    summary="Obtener metadatos completos y recursos de un dataset por ID o slug.",
    params_model=DatasetArgs,
    keywords=["dataset", "detalle", "recursos", "metadatos", "package_show"],
)
async def get_dataset(id: str) -> dict[str, Any]:
    result, cached, url = await client.package_show(id)
    return envelope(_slim_dataset(result), api="catalogodatos.gub.uy", url=url, cached=cached)


@tool(
    name="catalogo_list_organizations",
    module=MODULE,
    summary="Listar organizaciones que publican datos (ministerios, entes, intendencias).",
    params_model=OrganizationsArgs,
    keywords=["organizaciones", "ministerios", "entes", "publicadores", "organization"],
)
async def list_organizations(query: str | None = None, limit: int = 50) -> dict[str, Any]:
    params: dict[str, Any] = {"all_fields": True, "limit": limit}
    if query:
        params["q"] = query
    result, cached, url = await client.organization_list(params)
    orgs = [
        {"name": o.get("name"), "title": o.get("title"), "package_count": o.get("package_count")}
        for o in (result or [])
    ]
    return envelope(orgs, api="catalogodatos.gub.uy", url=url, cached=cached)


@tool(
    name="catalogo_list_groups",
    module=MODULE,
    summary="Listar categorías/grupos temáticos (salud, educación, transparencia, etc.).",
    params_model=GroupsArgs,
    keywords=["categorias", "grupos", "temas", "groups", "topics"],
)
async def list_groups(limit: int = 50) -> dict[str, Any]:
    result, cached, url = await client.group_list({"all_fields": True, "limit": limit})
    groups = [
        {"name": g.get("name"), "title": g.get("title"), "package_count": g.get("package_count")}
        for g in (result or [])
    ]
    return envelope(groups, api="catalogodatos.gub.uy", url=url, cached=cached)


@tool(
    name="catalogo_query_datastore",
    module=MODULE,
    summary="Consultar los registros tabulares de un recurso con datastore activo.",
    params_model=DatastoreSearchArgs,
    keywords=["datastore", "registros", "filas", "tabla", "query", "datos"],
)
async def query_datastore(
    resource_id: str,
    query: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    params: dict[str, Any] = {"resource_id": resource_id, "limit": limit, "offset": offset}
    if query:
        params["q"] = query
    result, cached, url = await client.datastore_search(params)
    return envelope(
        {
            "total": result.get("total"),
            "fields": result.get("fields"),
            "records": result.get("records"),
        },
        api="catalogodatos.gub.uy",
        url=url,
        cached=cached,
    )


@tool(
    name="catalogo_datastore_sql",
    module=MODULE,
    summary=(
        "Ejecutar una consulta SQL de solo lectura (SELECT) sobre el datastore "
        "de un recurso del Catálogo Nacional (CKAN datastore_search_sql)."
    ),
    params_model=DatastoreSqlArgs,
    keywords=["sql", "datastore", "select", "consulta", "query", "tabla", "ckan", "datos"],
)
async def datastore_sql(sql: str) -> dict[str, Any]:
    clean = _guard_sql(sql)
    result, cached, url = await client.datastore_search_sql(clean)
    return envelope(
        {
            "sql": result.get("sql"),
            "fields": result.get("fields"),
            "records": result.get("records"),
        },
        api="catalogodatos.gub.uy",
        url=url,
        cached=cached,
    )


@tool(
    name="catalogo_list_tags",
    module=MODULE,
    summary=(
        "Listar etiquetas (tags) del Catálogo Nacional de Datos Abiertos, "
        "opcionalmente filtradas por texto."
    ),
    params_model=TagsArgs,
    keywords=["tags", "etiquetas", "tag_list", "temas", "palabras clave"],
)
async def list_tags(query: str | None = None, limit: int = DEFAULT_ROWS) -> dict[str, Any]:
    # tag_list ignores a server-side 'limit'; send only 'query' and slice locally.
    params: dict[str, Any] = {}
    if query:
        params["query"] = query
    result, cached, url = await client.tag_list(params)
    tags = list(result or [])[:limit]
    return envelope(
        {"count": len(tags), "tags": tags},
        api="catalogodatos.gub.uy",
        url=url,
        cached=cached,
    )


@tool(
    name="catalogo_recent_datasets",
    module=MODULE,
    summary=(
        "Listar los datasets modificados más recientemente en el Catálogo "
        "Nacional (orden metadata_modified desc)."
    ),
    params_model=RecentDatasetsArgs,
    keywords=[
        "recientes",
        "novedades",
        "ultimos",
        "modificados",
        "recent",
        "datasets",
        "actualizados",
    ],
)
async def recent_datasets(limit: int = DEFAULT_ROWS) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": "*:*",
        "rows": limit,
        "sort": "metadata_modified desc",
    }
    result, cached, url = await client.package_search(params)
    return envelope(
        {
            "count": result.get("count"),
            "results": [_slim_dataset(p) for p in result.get("results", [])],
        },
        api="catalogodatos.gub.uy",
        url=url,
        cached=cached,
    )


@tool(
    name="catalogo_resource_show",
    module=MODULE,
    summary=(
        "Obtener los metadatos completos de un recurso (resource) por su ID, "
        "incluido si tiene datastore activo."
    ),
    params_model=ResourceArgs,
    keywords=["recurso", "resource", "resource_show", "metadatos", "datastore", "archivo"],
)
async def resource_show(resource_id: str) -> dict[str, Any]:
    result, cached, url = await client.resource_show(resource_id)
    slim = {
        "id": result.get("id"),
        "name": result.get("name"),
        "description": result.get("description"),
        "format": result.get("format"),
        "mimetype": result.get("mimetype"),
        "url": result.get("url"),
        "size": result.get("size"),
        "datastore_active": result.get("datastore_active", False),
        "package_id": result.get("package_id"),
        "created": result.get("created"),
        "last_modified": result.get("last_modified"),
        "metadata_modified": result.get("metadata_modified"),
    }
    return envelope(slim, api="catalogodatos.gub.uy", url=url, cached=cached)
