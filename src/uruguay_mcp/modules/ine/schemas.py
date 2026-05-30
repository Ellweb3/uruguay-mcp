"""Pydantic argument models for INE (ANDA/NADA) tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import (
    DEFAULT_DATASTORE_ROWS,
    DEFAULT_ROWS,
    MAX_DATASTORE_ROWS,
    MAX_ROWS,
)


class SearchStudiesArgs(BaseModel):
    query: str = Field(
        "", description="Texto de búsqueda libre (ej. 'censo', 'hogares', 'precios')."
    )
    rows: int = Field(
        DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de resultados por página."
    )
    page: int = Field(1, ge=1, description="Número de página (empieza en 1).")
    year_from: int | None = Field(None, description="Filtrar por año inicial del estudio.")
    year_to: int | None = Field(None, description="Filtrar por año final del estudio.")
    sort_by: str | None = Field(
        None, description="Ordenar por: 'year', 'title', 'nation' o 'popularity'."
    )
    sort_order: str = Field("desc", description="Orden: 'asc' o 'desc'.")


class GetStudyArgs(BaseModel):
    idno: str = Field(
        ...,
        description=(
            "El idno ANDA del estudio (cadena, p.ej. 'URY-INE-...-v01'). "
            "NO es el id numérico que aparece en la búsqueda."
        ),
    )


class ListCkanDatasetsArgs(BaseModel):
    query: str = Field("", description="Texto de búsqueda libre dentro de los datasets del INE.")
    rows: int = Field(
        DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de datasets a devolver."
    )
    start: int = Field(0, ge=0, description="Desplazamiento para paginación.")


class FindDataResourcesArgs(BaseModel):
    theme: str = Field(
        "",
        description=(
            "Texto de búsqueda libre para acotar los datasets del INE "
            "(ej. 'precios', 'empleo', 'poblacion'). Vacío = todos."
        ),
    )
    rows: int = Field(
        DEFAULT_ROWS,
        ge=1,
        le=MAX_ROWS,
        description="Cantidad de datasets del INE a inspeccionar.",
    )
    start: int = Field(0, ge=0, description="Desplazamiento para paginación de datasets.")


class DatastoreQueryArgs(BaseModel):
    resource_id: str = Field(
        ...,
        description=(
            "El id del recurso CKAN con DataStore activo "
            "(obtenelo con ine_find_data_resources)."
        ),
    )
    limit: int = Field(
        DEFAULT_DATASTORE_ROWS,
        ge=1,
        le=MAX_DATASTORE_ROWS,
        description="Cantidad de filas a devolver.",
    )
    offset: int = Field(0, ge=0, description="Desplazamiento de filas para paginación.")
    q: str | None = Field(
        None, description="Texto de búsqueda libre dentro de las filas del recurso."
    )


class DatastoreFieldsArgs(BaseModel):
    resource_id: str = Field(
        ...,
        description=(
            "El id del recurso CKAN con DataStore activo "
            "(obtenelo con ine_find_data_resources)."
        ),
    )


class DatasetResourcesArgs(BaseModel):
    dataset_name: str = Field(
        ...,
        description=(
            "El 'name' (slug) o id del dataset CKAN del INE "
            "(p.ej. 'ine-precios'), tal como aparece en ine_list_ckan_datasets."
        ),
    )
