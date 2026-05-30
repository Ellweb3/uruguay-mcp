"""Discoverable tools for the health (salud) module (CKAN-backed)."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

from ...shared import errors
from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import (
    API_NAME,
    MAX_CSV_ROWS,
    MEDICAMENTOS_DATASET,
    MODULE,
    POLICLINICAS_DATASET,
    SALUD_GROUP,
)
from .schemas import (
    BuscarArgs,
    DatasetArgs,
    DatastoreQueryArgs,
    MedicamentosArgs,
    PoliclinicasArgs,
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


def _datastore_resources(pkg: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the resources of a package that have an active datastore."""
    return [
        r
        for r in pkg.get("resources", [])
        if r.get("datastore_active") and r.get("id")
    ]


@tool(
    name="salud_buscar",
    module=MODULE,
    summary=(
        "Buscar datasets de salud en el Catálogo Nacional de Datos Abiertos (CKAN). "
        "Por defecto descubre por grupo 'salud' (276 datasets: MSP, FNR, ASSE, "
        "intendencias…), con filtro opcional por organización (msp | "
        "fondo-nacional-de-recursos) y texto libre."
    ),
    params_model=BuscarArgs,
    keywords=[
        "salud",
        "health",
        "msp",
        "fnr",
        "buscar",
        "search",
        "dataset",
        "ckan",
        "uruguay",
    ],
)
async def buscar(
    q: str = "",
    org: str | None = None,
    rows: int = 20,
    start: int = 0,
) -> dict[str, Any]:
    clauses = [f"groups:{SALUD_GROUP}"]
    if org:
        clauses.append(f"organization:{org}")
    params: dict[str, Any] = {
        "q": q or "*:*",
        "fq": " ".join(clauses),
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
    name="salud_get_dataset",
    module=MODULE,
    summary=(
        "Obtener metadatos completos de un dataset de salud por slug/id "
        "(package_show). Lista cada recurso con id, formato, URL de descarga y "
        "el flag datastore_active, para saber qué se puede consultar vs descargar."
    ),
    params_model=DatasetArgs,
    keywords=[
        "salud",
        "dataset",
        "package_show",
        "resource",
        "metadata",
        "detalle",
    ],
)
async def get_dataset(id: str) -> dict[str, Any]:
    result, cached, url = await client.package_show(id)
    return envelope(_slim_dataset(result), api=API_NAME, url=url, cached=cached)


@tool(
    name="salud_policlinicas",
    module=MODULE,
    summary=(
        "Devolver el dataset de ubicación de policlínicas (ubicacion-de-policlinicas, "
        "intendencia de Montevideo). Su CSV NO tiene datastore activo: por defecto "
        "resuelve el dataset y devuelve la URL de descarga del CSV; con download=true "
        "descarga y parsea las filas del CSV."
    ),
    params_model=PoliclinicasArgs,
    keywords=[
        "policlinicas",
        "ubicacion",
        "clinics",
        "locations",
        "policlinica",
        "montevideo",
        "salud",
    ],
)
async def policlinicas(download: bool = False) -> dict[str, Any]:
    pkg, cached, url = await client.package_show(POLICLINICAS_DATASET)
    resources = pkg.get("resources", [])
    csv_res = next(
        (r for r in resources if (r.get("format") or "").upper() == "CSV"),
        None,
    )
    data: dict[str, Any] = {
        "dataset": pkg.get("name"),
        "title": pkg.get("title"),
        "organization": (pkg.get("organization") or {}).get("title"),
        "csv_url": (csv_res or {}).get("url"),
        "datastore_active": (csv_res or {}).get("datastore_active", False),
        "resources": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "format": r.get("format"),
                "url": r.get("url"),
            }
            for r in resources
        ],
    }

    if not download:
        return envelope(data, api=API_NAME, url=url, cached=cached)

    csv_url = data["csv_url"]
    if not csv_url:
        raise errors.NotFoundError(
            "El dataset de policlínicas no expone un recurso CSV descargable.",
            details={"api": API_NAME},
        )
    text, csv_cached, csv_url = await client.fetch_csv(csv_url)
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for i, row in enumerate(reader):
        if i >= MAX_CSV_ROWS:
            break
        rows.append(row)
    data["fields"] = reader.fieldnames or []
    data["count"] = len(rows)
    data["records"] = rows
    return envelope(data, api=API_NAME, url=csv_url, cached=cached and csv_cached)


@tool(
    name="salud_medicamentos",
    module=MODULE,
    summary=(
        "Consultar el gasto por tratamientos con medicamentos del FNR (dataset "
        "fondo-nacional-de-recursos…). NOTA: no existe un 'Formulario Terapéutico de "
        "Medicamentos' en este CKAN. Resuelve el recurso datastore-activo más "
        "reciente y lo consulta por texto/año/área, o con SQL para agregación."
    ),
    params_model=MedicamentosArgs,
    keywords=[
        "medicamentos",
        "tratamientos",
        "formulario terapeutico",
        "drugs",
        "fnr",
        "gasto",
        "farmacos",
        "medication",
    ],
)
async def medicamentos(
    q: str | None = None,
    anio: int | None = None,
    area: str | None = None,
    limit: int = 50,
    sql: str | None = None,
) -> dict[str, Any]:
    pkg, cached, pkg_url = await client.package_show(MEDICAMENTOS_DATASET)
    actives = _datastore_resources(pkg)
    if not actives:
        raise errors.NotFoundError(
            "El dataset de medicamentos del FNR no tiene recursos con datastore "
            "activo para consultar.",
            details={"api": API_NAME},
        )
    # Pick the most recently modified datastore-active resource.
    resource = max(actives, key=lambda r: r.get("last_modified") or "")
    resource_id = resource["id"]

    if sql:
        clean = _guard_sql(sql)
        result, q_cached, url = await client.datastore_search_sql(clean)
        return envelope(
            {
                "resource_id": resource_id,
                "sql": result.get("sql"),
                "fields": result.get("fields"),
                "records": result.get("records"),
            },
            api=API_NAME,
            url=url,
            cached=cached and q_cached,
        )

    filters: dict[str, Any] = {}
    if anio is not None:
        filters["Anio"] = anio
    if area:
        filters["Area_prestacion"] = area
    params: dict[str, Any] = {"resource_id": resource_id, "limit": limit}
    if q:
        params["q"] = q
    if filters:
        params["filters"] = json.dumps(filters, ensure_ascii=False)
    result, q_cached, url = await client.datastore_search(params)
    return envelope(
        {
            "resource_id": resource_id,
            "total": result.get("total"),
            "fields": result.get("fields"),
            "records": result.get("records"),
        },
        api=API_NAME,
        url=url,
        cached=cached and q_cached,
    )


@tool(
    name="salud_datastore_query",
    module=MODULE,
    summary=(
        "Escape hatch genérico: ejecutar datastore_search (o datastore_search_sql si "
        "se provee sql) sobre cualquier recurso con datastore activo descubierto vía "
        "salud_get_dataset. Cubre vacunación, egresos hospitalarios, ELEPEM, "
        "solicitudes/actos médicos del FNR, etc."
    ),
    params_model=DatastoreQueryArgs,
    keywords=[
        "datastore",
        "query",
        "sql",
        "vacunacion",
        "egresos",
        "elepem",
        "fnr",
        "records",
        "tabular",
    ],
)
async def datastore_query(
    resource_id: str,
    q: str | None = None,
    filters: dict[str, Any] | None = None,
    fields: str | None = None,
    sort: str | None = None,
    limit: int = 100,
    offset: int = 0,
    sql: str | None = None,
) -> dict[str, Any]:
    if sql:
        clean = _guard_sql(sql)
        result, cached, url = await client.datastore_search_sql(clean)
        return envelope(
            {
                "sql": result.get("sql"),
                "fields": result.get("fields"),
                "records": result.get("records"),
            },
            api=API_NAME,
            url=url,
            cached=cached,
        )

    params: dict[str, Any] = {
        "resource_id": resource_id,
        "limit": limit,
        "offset": offset,
    }
    if q:
        params["q"] = q
    if filters:
        params["filters"] = json.dumps(filters, ensure_ascii=False)
    if fields:
        params["fields"] = fields
    if sort:
        params["sort"] = sort
    result, cached, url = await client.datastore_search(params)
    return envelope(
        {
            "total": result.get("total"),
            "fields": result.get("fields"),
            "records": result.get("records"),
        },
        api=API_NAME,
        url=url,
        cached=cached,
    )
