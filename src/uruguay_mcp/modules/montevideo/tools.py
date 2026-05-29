"""Discoverable tools for the Intendencia de Montevideo (open data + transport)."""

from __future__ import annotations

import re
from typing import Any

from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import (
    CKAN_API_NAME,
    MAX_BUS_RESULTS,
    MODULE,
    MULTAS_DATASET_SLUG,
    TRANSPORT_API_NAME,
)
from .schemas import (
    BusesNearArgs,
    BusEtaArgs,
    BusPositionsArgs,
    BusStopLinesArgs,
    BusStopsArgs,
    DatasetArgs,
    DatastoreSearchArgs,
    GroupsArgs,
    MultasTransitoArgs,
    OrganizationsArgs,
    SearchDatasetsArgs,
)

_YEAR_RE = re.compile(r"(19|20)\d{2}")


# --- CKAN slimmers --------------------------------------------------------
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


# --- Transport slimmers ---------------------------------------------------
def _slim_vehicle(v: dict[str, Any]) -> dict[str, Any]:
    """Project a transport VehicleItem to the useful fields."""
    return {
        "id": v.get("id"),
        "line": v.get("line"),
        "lineVariantId": v.get("lineVariantId"),
        "origin": v.get("origin"),
        "destination": v.get("destination"),
        "subline": v.get("subline"),
        "companyName": v.get("companyName"),
        "vehicleType": v.get("vehicleType"),
        "timestamp": v.get("timestamp"),
        "location": v.get("location"),
        "special": v.get("special"),
        "access": v.get("access"),
    }


def _slim_eta(e: dict[str, Any]) -> dict[str, Any]:
    """Project an ETAItem to the useful fields (eta units pass through raw)."""
    return {
        "busId": e.get("busId"),
        "line": e.get("line"),
        "lineVariantId": e.get("lineVariantId"),
        "origin": e.get("origin"),
        "destination": e.get("destination"),
        "subline": e.get("subline"),
        "eta": e.get("eta"),
        "distance": e.get("distance"),
        "location": e.get("location"),
        "companyName": e.get("companyName"),
        "access": e.get("access"),
    }


def _slim_busstop(s: dict[str, Any]) -> dict[str, Any]:
    return {
        "busstopId": s.get("busstopId"),
        "street1": s.get("street1"),
        "street2": s.get("street2"),
        "street1Id": s.get("street1Id"),
        "street2Id": s.get("street2Id"),
        "location": s.get("location"),
    }


def _as_list(value: Any) -> list[dict[str, Any]]:
    return [x for x in (value or []) if isinstance(x, dict)]


# --- CKAN tools -----------------------------------------------------------
@tool(
    name="montevideo_search_datasets",
    module=MODULE,
    summary=(
        "Buscar datasets en el Portal de Datos Abiertos de la Intendencia de "
        "Montevideo (CKAN)."
    ),
    params_model=SearchDatasetsArgs,
    keywords=[
        "montevideo", "intendencia", "datos abiertos", "dataset", "ckan", "buscar", "search",
    ],
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
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="montevideo_get_dataset",
    module=MODULE,
    summary="Obtener metadatos completos y recursos de un dataset de Montevideo por ID o slug.",
    params_model=DatasetArgs,
    keywords=["montevideo", "dataset", "detalle", "recursos", "package_show"],
)
async def get_dataset(id: str) -> dict[str, Any]:
    result, cached, url = await client.package_show(id)
    return envelope(_slim_dataset(result), api=CKAN_API_NAME, url=url, cached=cached)


@tool(
    name="montevideo_list_organizations",
    module=MODULE,
    summary="Listar organizaciones/dependencias que publican datos en el portal de Montevideo.",
    params_model=OrganizationsArgs,
    keywords=["montevideo", "organizaciones", "dependencias", "organization"],
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
    return envelope(orgs, api=CKAN_API_NAME, url=url, cached=cached)


@tool(
    name="montevideo_list_groups",
    module=MODULE,
    summary="Listar categorías/grupos temáticos del portal de Montevideo.",
    params_model=GroupsArgs,
    keywords=["montevideo", "categorias", "grupos", "temas", "groups"],
)
async def list_groups(limit: int = 50) -> dict[str, Any]:
    result, cached, url = await client.group_list({"all_fields": True, "limit": limit})
    groups = [
        {"name": g.get("name"), "title": g.get("title"), "package_count": g.get("package_count")}
        for g in (result or [])
    ]
    return envelope(groups, api=CKAN_API_NAME, url=url, cached=cached)


@tool(
    name="montevideo_query_datastore",
    module=MODULE,
    summary="Consultar registros tabulares de un recurso con datastore activo (Montevideo).",
    params_model=DatastoreSearchArgs,
    keywords=["montevideo", "datastore", "registros", "tabla", "query"],
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
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )


def _resource_years(resource: dict[str, Any]) -> list[int]:
    text = f"{resource.get('name') or ''} {resource.get('description') or ''}"
    return sorted({int(m.group()) for m in _YEAR_RE.finditer(text)})


def _slim_resource(r: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": r.get("id"),
        "name": r.get("name"),
        "format": r.get("format"),
        "url": r.get("url"),
        "years": _resource_years(r),
    }


@tool(
    name="montevideo_multas_transito",
    module=MODULE,
    summary=(
        "Índice de los datos abiertos de multas de tránsito (SUCIVE) de la "
        "Intendencia de Montevideo: archivos anuales descargables y tablas de "
        "referencia (ordenanzas, tipos de vehículo, origen de la multa). Son "
        "datos AGREGADOS/estadísticos, NO una consulta de deuda por vehículo "
        "(eso requiere matrícula+padrón y reCAPTCHA en sucive.gub.uy)."
    ),
    params_model=MultasTransitoArgs,
    keywords=[
        "sucive", "multas", "transito", "infracciones", "patente", "vehiculos",
        "montevideo", "estadistica", "fines",
    ],
)
async def multas_transito(year: int | None = None) -> dict[str, Any]:
    result, cached, url = await client.package_show(MULTAS_DATASET_SLUG)
    resources = result.get("resources", [])

    annual: list[dict[str, Any]] = []
    reference: list[dict[str, Any]] = []
    for r in resources:
        slim = _slim_resource(r)
        (annual if slim["years"] else reference).append(slim)

    if year is not None:
        annual = [r for r in annual if year in r["years"]]

    return envelope(
        {
            "dataset": {
                "title": result.get("title"),
                "name": result.get("name"),
                "notes": result.get("notes"),
                "metadata_modified": result.get("metadata_modified"),
            },
            "note": (
                "Datos estadísticos de multas (no consulta de deuda por vehículo). "
                "Recursos sin datastore: descargá los CSV/ZIP desde 'url'."
            ),
            "annual_files": sorted(annual, key=lambda r: r["years"]),
            "reference_tables": reference,
        },
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )


# --- Transport tools ------------------------------------------------------
@tool(
    name="montevideo_bus_eta",
    module=MODULE,
    summary=(
        "Tiempo estimado de arribo (TEA/ETA) de los próximos buses a una parada de "
        "Montevideo. Requiere la parada y al menos una línea. Unidad de 'eta' no "
        "documentada (segundos o minutos): se devuelve sin transformar."
    ),
    params_model=BusEtaArgs,
    keywords=[
        "montevideo", "bus", "omnibus", "parada", "eta", "tea", "llegada", "tiempo", "proximo",
    ],
)
async def bus_eta(
    busstop_id: int,
    lines: list[str],
    amount_per_line: int = 1,
    line_variant_ids: list[int] | None = None,
) -> dict[str, Any]:
    result, cached, url = await client.upcoming_buses(
        busstop_id, lines, amount_per_line, line_variant_ids
    )
    items = [_slim_eta(e) for e in _as_list(result)]
    return envelope(items, api=TRANSPORT_API_NAME, url=url, cached=cached)


@tool(
    name="montevideo_bus_positions",
    module=MODULE,
    summary=(
        "Posiciones en tiempo real de los buses de Montevideo, filtrables por "
        "línea, empresa o parada."
    ),
    params_model=BusPositionsArgs,
    keywords=[
        "montevideo", "bus", "omnibus", "posicion", "tiempo real", "ubicacion", "gps", "tracking",
    ],
)
async def bus_positions(
    lines: list[str] | None = None,
    company: str | None = None,
    busstop_id: int | None = None,
    line_variant_ids: list[int] | None = None,
    bus_id: int | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "lines": ",".join(lines) if lines else None,
        "company": company,
        "busstopId": busstop_id,
        "lineVariantIds": ",".join(str(v) for v in line_variant_ids) if line_variant_ids else None,
        "busId": bus_id,
    }
    result, cached, url = await client.bus_positions(params)
    items = [_slim_vehicle(v) for v in _as_list(result)]
    return envelope(items, api=TRANSPORT_API_NAME, url=url, cached=cached)


@tool(
    name="montevideo_buses_near",
    module=MODULE,
    summary=(
        "Buses de Montevideo en tiempo real dentro de un radio (metros) de un "
        "punto geográfico."
    ),
    params_model=BusesNearArgs,
    keywords=["montevideo", "bus", "cerca", "geografico", "radio", "near", "ubicacion"],
)
async def buses_near(lat: float, lng: float, radius_m: float) -> dict[str, Any]:
    center = f"{lat},{lng}"
    result, cached, url = await client.buses_geo(center, radius_m)
    items = [_slim_vehicle(v) for v in _as_list(result)]
    return envelope(items, api=TRANSPORT_API_NAME, url=url, cached=cached)


@tool(
    name="montevideo_list_busstops",
    module=MODULE,
    summary="Listar/buscar paradas de ómnibus de Montevideo (id, calles, ubicación).",
    params_model=BusStopsArgs,
    keywords=["montevideo", "parada", "busstop", "paradas", "omnibus"],
)
async def list_busstops(
    query: str | None = None, limit: int = MAX_BUS_RESULTS
) -> dict[str, Any]:
    result, cached, url = await client.list_busstops()
    stops = [_slim_busstop(s) for s in _as_list(result)]
    if query:
        needle = query.lower()
        stops = [
            s
            for s in stops
            if needle in f"{s.get('street1') or ''} {s.get('street2') or ''}".lower()
        ]
    return envelope(stops[:limit], api=TRANSPORT_API_NAME, url=url, cached=cached)


@tool(
    name="montevideo_busstop_lines",
    module=MODULE,
    summary=(
        "Líneas de ómnibus que pasan por una parada de Montevideo (útil para "
        "montevideo_bus_eta)."
    ),
    params_model=BusStopLinesArgs,
    keywords=["montevideo", "parada", "lineas", "busstop", "lines"],
)
async def busstop_lines(busstop_id: int) -> dict[str, Any]:
    result, cached, url = await client.busstop_lines(busstop_id)
    lines = [
        {"line": x.get("line"), "lineId": x.get("lineId")} for x in _as_list(result)
    ]
    return envelope(lines, api=TRANSPORT_API_NAME, url=url, cached=cached)
