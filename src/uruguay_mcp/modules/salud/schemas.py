"""Pydantic argument models for salud tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .constants import DEFAULT_ROWS, MAX_ROWS


class BuscarArgs(BaseModel):
    q: str = Field("", description="Texto de búsqueda libre (ej. 'vacunación', 'egresos').")
    org: Literal["msp", "fondo-nacional-de-recursos"] | None = Field(
        None,
        description=(
            "Filtro opcional por organización: 'msp' (Ministerio de Salud "
            "Pública) o 'fondo-nacional-de-recursos' (FNR)."
        ),
    )
    rows: int = Field(DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de resultados.")
    start: int = Field(0, ge=0, description="Desplazamiento para paginación.")


class DatasetArgs(BaseModel):
    id: str = Field(..., description="ID o slug del dataset de salud (campo 'name' o 'id').")


class PoliclinicasArgs(BaseModel):
    download: bool = Field(
        False,
        description=(
            "Si es true, descarga y parsea las filas del CSV de policlínicas "
            "(no tiene datastore activo). Si es false, solo devuelve la URL."
        ),
    )


class MedicamentosArgs(BaseModel):
    q: str | None = Field(
        None,
        description="Texto libre (ej. nombre de prestación/tratamiento) sobre los registros.",
    )
    anio: int | None = Field(None, description="Filtrar por año (columna 'Anio').")
    area: str | None = Field(
        None, description="Filtrar por área de prestación (columna 'Area_prestacion')."
    )
    limit: int = Field(50, ge=1, le=MAX_ROWS, description="Cantidad de registros.")
    sql: str | None = Field(
        None,
        description=(
            "Consulta SELECT de solo lectura opcional para agregación. La tabla es "
            'el resource_id entre comillas dobles y las columnas también, ej: '
            'SELECT "Area_prestacion", count(*) FROM "<rid>" GROUP BY "Area_prestacion".'
        ),
    )


class DatastoreQueryArgs(BaseModel):
    resource_id: str = Field(
        ..., description="ID (uuid) del recurso con datastore activo (vía salud_get_dataset)."
    )
    q: str | None = Field(None, description="Texto de búsqueda dentro de los registros.")
    filters: dict[str, str | int | float] | None = Field(
        None, description="Filtros exactos por campo, ej: {'Anio': 2020}."
    )
    fields: str | None = Field(
        None, description="Lista de campos a devolver, separados por coma."
    )
    sort: str | None = Field(
        None, description="Orden, ej: 'Anio desc' o 'Importe desc'."
    )
    limit: int = Field(100, ge=1, le=MAX_ROWS, description="Cantidad de registros.")
    offset: int = Field(0, ge=0, description="Desplazamiento para paginación.")
    sql: str | None = Field(
        None,
        description=(
            "Consulta SELECT de solo lectura opcional. Si se provee, se usa "
            "datastore_search_sql en lugar de datastore_search."
        ),
    )
