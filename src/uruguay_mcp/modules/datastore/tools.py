"""Discoverable tools for the cross-source local datastore.

Load tabular data from any source into a local SQLite database, then run
read-only SQL across the loaded tables — the cross-API JOIN feature.
"""

from __future__ import annotations

from typing import Any

from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import API_NAME, DEFAULT_CKAN_BASE, MAX_ROWS, MODULE
from .schemas import (
    ListTablesArgs,
    LoadCkanResourceArgs,
    LoadCsvArgs,
    SqlArgs,
)


@tool(
    name="datastore_load_csv",
    module=MODULE,
    summary="Descargar un CSV desde una URL y cargarlo en una tabla SQLite local.",
    params_model=LoadCsvArgs,
    keywords=["csv", "cargar", "importar", "tabla", "sqlite", "datos", "load"],
)
async def load_csv(url: str, table: str, max_rows: int = MAX_ROWS) -> dict[str, Any]:
    summary = await client.load_csv_url(url, table, max_rows)
    return envelope(summary, api=API_NAME, url=url)


@tool(
    name="datastore_load_ckan_resource",
    module=MODULE,
    summary="Cargar un recurso CKAN (datastore_search) en una tabla SQLite local.",
    params_model=LoadCkanResourceArgs,
    keywords=["ckan", "recurso", "datastore", "cargar", "tabla", "importar", "catalogo"],
)
async def load_ckan_resource(
    resource_id: str,
    table: str,
    base: str = DEFAULT_CKAN_BASE,
    max_rows: int = MAX_ROWS,
) -> dict[str, Any]:
    summary = await client.load_ckan_resource(resource_id, table, base, max_rows)
    return envelope(summary, api=API_NAME, url=summary.get("source_url"))


@tool(
    name="datastore_sql",
    module=MODULE,
    summary="Ejecutar una consulta SELECT de sólo lectura sobre las tablas cargadas (JOINs).",
    params_model=SqlArgs,
    keywords=["sql", "select", "consulta", "join", "unir", "query", "cross"],
)
async def datastore_sql(query: str) -> dict[str, Any]:
    result = client.run_select(query)
    return envelope(result, api=API_NAME, extra={"query": query})


@tool(
    name="datastore_list_tables",
    module=MODULE,
    summary="Listar las tablas cargadas con su cantidad de filas y columnas.",
    params_model=ListTablesArgs,
    keywords=["tablas", "listar", "esquema", "columnas", "filas", "tables", "schema"],
)
async def list_tables() -> dict[str, Any]:
    tables = client.list_tables()
    return envelope({"tables": tables, "count": len(tables)}, api=API_NAME)
