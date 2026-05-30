"""Pydantic argument models for parlamento tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them claras y en español.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import DEFAULT_ROWS, MAX_ROWS


class BuscarArgs(BaseModel):
    query: str = Field(
        "",
        description=(
            "Texto de búsqueda libre (ej. 'asistencias', 'pedidos de informes', "
            "'leyes'). Vacío devuelve todos los datasets del Parlamento."
        ),
    )
    rows: int = Field(DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de resultados.")
    start: int = Field(0, ge=0, description="Desplazamiento para paginación.")


class GetDatasetArgs(BaseModel):
    id: str = Field(
        ...,
        description=(
            "Slug o uuid del dataset (ej. "
            "'parlamento-del-uruguay-asistencias-a-la-camara-de-representantes')."
        ),
    )


class AsistenciasArgs(BaseModel):
    camara: str = Field(
        "representantes",
        description="Cámara: 'representantes' (Diputados) o 'senadores'.",
    )
    legislatura: int | None = Field(
        None,
        description=(
            "Número de legislatura (50=2025-2030, 49=2020-2025, 48, 47, 46). "
            "Si se omite, usa la legislatura más reciente con datos consultables."
        ),
    )
    query: str | None = Field(
        None, description="Texto de búsqueda dentro de los registros (opcional)."
    )
    limit: int = Field(DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de registros.")
    offset: int = Field(0, ge=0, description="Desplazamiento para paginación.")


class ActividadesArgs(BaseModel):
    camara: str = Field(
        "senado",
        description="Cámara: 'senado' o 'representantes' (Diputados).",
    )
    legislatura: int | None = Field(
        None,
        description=(
            "Número de legislatura (50, 49, 48, 47, 46, 45). Si se omite, usa la "
            "más reciente con datos consultables."
        ),
    )
    query: str | None = Field(
        None, description="Texto de búsqueda dentro de los registros (opcional)."
    )
    limit: int = Field(DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de registros.")
    offset: int = Field(0, ge=0, description="Desplazamiento para paginación.")
