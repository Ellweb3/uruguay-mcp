"""Pydantic argument models for gubuy tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import DEFAULT_LIMIT, DEFAULT_ROWS, MAX_LIMIT, MAX_ROWS


class ListServiciosArgs(BaseModel):
    query: str = Field(
        "", description="Filtro de texto libre sobre título y descripción (cliente)."
    )
    tag: str | None = Field(None, description="Filtrar por etiqueta (cliente).")
    limit: int = Field(
        DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Cantidad máxima de servicios."
    )
    start: int = Field(0, ge=0, description="Desplazamiento para paginación (cliente).")


class GetServicioArgs(BaseModel):
    id: str = Field(..., description="UUID o slug del showcase/servicio (requerido).")


class ServicioDatasetsArgs(BaseModel):
    showcase_id: str = Field(
        ..., description="UUID o slug del servicio/showcase (requerido)."
    )


class SearchApisArgs(BaseModel):
    query: str = Field("", description="Texto de búsqueda libre (ej. 'transporte').")
    rows: int = Field(DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de resultados.")
    start: int = Field(0, ge=0, description="Desplazamiento para paginación.")
