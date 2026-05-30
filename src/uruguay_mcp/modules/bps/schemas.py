"""Pydantic argument models for BPS (Observatorio / BPS en Cifras) tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import MAX_ROWS


class ListarCategoriasArgs(BaseModel):
    incluir_pruebas: bool = Field(
        False,
        description=(
            "Si es True, incluye los nodos de prueba/conmemorativos del menú "
            "(p.ej. 'Pagina de Prueba', 'Día internacional...'). Por defecto se "
            "filtran."
        ),
    )


class ListarPanelesArgs(BaseModel):
    pass


class IndicadorArgs(BaseModel):
    bloque: int = Field(..., description="El id del bloque del indicador a consultar.")
    pagina: int = Field(1, ge=1, description="El id de la página (por defecto 1).")
    max_filas: int = Field(
        MAX_ROWS,
        ge=1,
        le=MAX_ROWS,
        description="Máximo de filas de datos a devolver.",
    )


class BuscarIndicadorArgs(BaseModel):
    query: str = Field(
        ...,
        description=(
            "Texto a buscar en el nombre/descripción de los indicadores "
            "(ej. 'jubilaciones', 'pensiones', 'recaudación')."
        ),
    )
    max_resultados: int = Field(
        10, ge=1, le=50, description="Máximo de indicadores coincidentes a devolver."
    )


class SerieCsvArgs(BaseModel):
    id_pagina: int = Field(
        ...,
        description=(
            "El id de la página (id_pagina del indicador) cuyas series de datos "
            "se quieren descargar."
        ),
    )
    nombre: str | None = Field(
        None,
        description=(
            "Filtra los archivos de serie cuyo nombre contenga este texto. "
            "Vacío = todos los archivos de la página."
        ),
    )
    max_filas: int = Field(
        MAX_ROWS,
        ge=1,
        le=MAX_ROWS,
        description="Máximo de filas de datos a devolver por archivo de serie.",
    )
