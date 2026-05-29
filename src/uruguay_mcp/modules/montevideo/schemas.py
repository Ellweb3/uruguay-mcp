"""Pydantic argument models for the Montevideo tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import DEFAULT_ROWS, MAX_BUS_RESULTS, MAX_ROWS


# --- CKAN open-data portal ----------------------------------------------
class SearchDatasetsArgs(BaseModel):
    query: str = Field("", description="Texto de búsqueda libre (ej. 'arbolado', 'transito').")
    organization: str | None = Field(
        None, description="Filtrar por organización/dependencia (slug, ej. 'areas-verdes')."
    )
    group: str | None = Field(None, description="Filtrar por categoría/grupo temático.")
    tags: list[str] = Field(default_factory=list, description="Filtrar por etiquetas.")
    rows: int = Field(DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de resultados.")
    start: int = Field(0, ge=0, description="Desplazamiento para paginación.")


class DatasetArgs(BaseModel):
    id: str = Field(..., description="ID o slug del dataset (campo 'name' o 'id').")


class OrganizationsArgs(BaseModel):
    query: str | None = Field(None, description="Filtro opcional por nombre de organización.")
    limit: int = Field(50, ge=1, le=200, description="Cantidad máxima de organizaciones.")


class GroupsArgs(BaseModel):
    limit: int = Field(50, ge=1, le=200, description="Cantidad máxima de grupos/categorías.")


class DatastoreSearchArgs(BaseModel):
    resource_id: str = Field(..., description="ID del recurso (resource) con datastore activo.")
    query: str | None = Field(None, description="Texto de búsqueda dentro de los registros.")
    limit: int = Field(DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de registros.")
    offset: int = Field(0, ge=0, description="Desplazamiento para paginación.")


class MultasTransitoArgs(BaseModel):
    year: int | None = Field(
        None,
        ge=2000,
        le=2100,
        description="Filtrar los archivos anuales por año (ej. 2018). Vacío = todos.",
    )


# --- Public transport ---------------------------------------------------
class BusEtaArgs(BaseModel):
    busstop_id: int = Field(..., description="ID de la parada de ómnibus (busstopId).")
    lines: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Líneas a consultar (OBLIGATORIO, al menos una). Números de línea como "
            "strings, ej. ['103', '104']. Se envían separados por coma a la API."
        ),
    )
    amount_per_line: int = Field(
        1, ge=1, le=10, description="Cantidad de próximos buses por línea (default 1)."
    )
    line_variant_ids: list[int] | None = Field(
        None, description="IDs de variantes de línea (lineVariantIds) para filtrar (opcional)."
    )


class BusPositionsArgs(BaseModel):
    lines: list[str] | None = Field(
        None, description="Filtrar por líneas (números como strings, separados por coma)."
    )
    company: str | None = Field(None, description="Filtrar por empresa (companyName).")
    busstop_id: int | None = Field(None, description="Filtrar por parada (busstopId).")
    line_variant_ids: list[int] | None = Field(
        None, description="Filtrar por variantes de línea (lineVariantIds)."
    )
    bus_id: int | None = Field(None, description="Filtrar por un bus específico (busId).")


class BusesNearArgs(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitud del punto central.")
    lng: float = Field(..., ge=-180, le=180, description="Longitud del punto central.")
    radius_m: float = Field(..., gt=0, description="Radio de búsqueda en metros.")


class BusStopsArgs(BaseModel):
    query: str | None = Field(
        None, description="Filtro opcional (texto en nombres de calles) aplicado del lado cliente."
    )
    limit: int = Field(
        MAX_BUS_RESULTS, ge=1, le=MAX_BUS_RESULTS, description="Cantidad máxima de paradas."
    )


class BusStopLinesArgs(BaseModel):
    busstop_id: int = Field(..., description="ID de la parada de ómnibus (busstopId).")
