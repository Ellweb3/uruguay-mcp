"""Pydantic argument models for educacion (ANEP) tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .constants import DEFAULT_ROWS, MAX_ROWS


class BuscarArgs(BaseModel):
    q: str = Field(
        "", description="Texto de búsqueda libre dentro de los datasets de ANEP (opcional)."
    )
    rows: int = Field(DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de resultados.")
    start: int = Field(0, ge=0, description="Desplazamiento para paginación.")


class DatasetArgs(BaseModel):
    id: str = Field(
        ...,
        description=(
            "Slug o UUID del dataset de ANEP, ej. 'anep-centros-anep' o "
            "'anep-http-sig-anep-edu-uy-siganep-formatos'."
        ),
    )


class CentrosArgs(BaseModel):
    q: str | None = Field(
        None, description="Texto de búsqueda libre dentro de los registros (ej. 'ARTIGAS')."
    )
    departamento: str | None = Field(
        None, description="Filtrar por departamento (ej. 'MONTEVIDEO'). Sensible a mayúsculas."
    )
    localidad: str | None = Field(None, description="Filtrar por localidad.")
    subsistema: Literal["ces", "cfe", "789", "ceip", "cetp"] | None = Field(
        None,
        description=(
            "Subsistema de ANEP a consultar: 'ces' (Secundaria/DGES, por "
            "defecto), 'cfe' (Formación docente), '789' (7°/8°/9° rural). "
            "'ceip' (Primaria) y 'cetp' (UTU) NO tienen datastore: se devuelve "
            "la URL de descarga del XLSX en su lugar."
        ),
    )
    limit: int = Field(DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de registros.")
    offset: int = Field(0, ge=0, description="Desplazamiento para paginación.")
