"""Pydantic argument models for datastore tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import DEFAULT_CKAN_BASE, MAX_ROWS


class LoadCsvArgs(BaseModel):
    url: str = Field(..., description="URL del archivo CSV a descargar e importar.")
    table: str = Field(..., description="Nombre de la tabla destino (se sanitiza).")
    max_rows: int = Field(
        MAX_ROWS, ge=1, le=MAX_ROWS, description="Máximo de filas a importar."
    )


class LoadCkanResourceArgs(BaseModel):
    resource_id: str = Field(..., description="ID del recurso (resource) en el portal CKAN.")
    table: str = Field(..., description="Nombre de la tabla destino (se sanitiza).")
    base: str = Field(
        DEFAULT_CKAN_BASE, description="URL base del portal CKAN (por defecto catalogodatos)."
    )
    max_rows: int = Field(
        MAX_ROWS, ge=1, le=MAX_ROWS, description="Máximo de filas a importar."
    )


class SqlArgs(BaseModel):
    query: str = Field(
        ...,
        description=(
            "Consulta SQL de SÓLO LECTURA (una única sentencia SELECT). Se rechaza "
            "cualquier otra cosa (INSERT/UPDATE/DELETE/DROP/PRAGMA/ATTACH, etc.)."
        ),
    )


class ListTablesArgs(BaseModel):
    pass
