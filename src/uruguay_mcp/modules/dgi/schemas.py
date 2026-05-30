"""Pydantic argument models for DGI (Dirección General Impositiva) tools.

Estos modelos también son el JSON schema que ``discover_tools`` muestra al
modelo, así que las descripciones importan — mantenelas claras y en español.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import MAX_ROWS, PREVIEW_ROWS


class ListarDatosArgs(BaseModel):
    tema: str | None = Field(
        None,
        description=(
            "Filtra los archivos cuyo título contenga este texto (sin acentos / "
            "sin distinguir mayúsculas). Ej.: 'unidad indexada', 'IPC', "
            "'recargos', 'ITP'. Vacío = todos."
        ),
    )
    formato: str | None = Field(
        None,
        description=(
            "Filtra por formato de archivo (ods, xlsx, csv). Vacío = todos."
        ),
    )


class TablaArgs(BaseModel):
    url: str = Field(
        ...,
        description=(
            "URL del archivo de datos a parsear (debe ser de www.gub.uy y "
            "terminar en .ods, .xlsx o .csv). Usá la URL que devuelve "
            "dgi_listar_datos o dgi_buscar_valor."
        ),
    )
    hoja: int = Field(
        0,
        ge=0,
        description="Índice de la hoja a leer (0-based); los .ods suelen tener varias.",
    )
    max_filas: int = Field(
        MAX_ROWS,
        ge=1,
        le=MAX_ROWS,
        description="Máximo de filas no vacías a devolver.",
    )


class BuscarValorArgs(BaseModel):
    query: str = Field(
        ...,
        description=(
            "Tema a buscar en los títulos de los archivos de valores de "
            "referencia (ej. 'unidad indexada', 'IPC', 'recargos por mora', "
            "'ITP'). Se elige la mejor coincidencia, prefiriendo el período más "
            "reciente."
        ),
    )
    max_filas: int = Field(
        PREVIEW_ROWS,
        ge=1,
        le=MAX_ROWS,
        description="Máximo de filas de la vista previa de la tabla encontrada.",
    )


class BoletinesArgs(BaseModel):
    incluir_gasto: bool = Field(
        False,
        description=(
            "Si es True, incluye además los PDFs de gasto tributario; por "
            "defecto sólo los boletines estadísticos."
        ),
    )
