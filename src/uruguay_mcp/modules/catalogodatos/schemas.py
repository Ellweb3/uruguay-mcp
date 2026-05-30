"""Pydantic argument models for catalogodatos tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import DEFAULT_ROWS, MAX_ROWS


class SearchDatasetsArgs(BaseModel):
    query: str = Field("", description="Texto de búsqueda libre (ej. 'salud', 'presupuesto').")
    organization: str | None = Field(
        None, description="Filtrar por organización (slug, ej. 'ine')."
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


class DatastoreSqlArgs(BaseModel):
    sql: str = Field(
        ...,
        description=(
            "Consulta SELECT de solo lectura sobre el datastore. La tabla es el "
            'resource_id entre comillas dobles, ej: SELECT * FROM "<resource_id>" '
            "LIMIT 50. No se permiten múltiples sentencias, comentarios ni DDL/DML."
        ),
    )


class TagsArgs(BaseModel):
    query: str | None = Field(
        None, description="Filtro de subcadena sobre los tags (ej. 'salud')."
    )
    limit: int = Field(
        DEFAULT_ROWS,
        ge=1,
        le=MAX_ROWS,
        description="Cantidad máxima de etiquetas (recortado del lado del cliente).",
    )


class RecentDatasetsArgs(BaseModel):
    limit: int = Field(
        DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de datasets recientes."
    )


class ResourceArgs(BaseModel):
    resource_id: str = Field(..., description="ID del recurso (resource).")
