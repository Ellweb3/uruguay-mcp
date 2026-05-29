"""Pydantic argument models for INE (ANDA/NADA) tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import DEFAULT_ROWS, MAX_ROWS


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
