"""Pydantic argument models for the noticias (gub.uy) tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import (
    DEFAULT_LIMIT,
    DEFAULT_SEARCH_LIMIT,
    DEFAULT_SUBSITE,
    MAX_LIMIT,
    MAX_SEARCH_LIMIT,
)


class RecientesArgs(BaseModel):
    subsite: str = Field(
        DEFAULT_SUBSITE,
        description=(
            "Subsitio de gub.uy a consultar (slug). Ej: 'presidencia', "
            "'ministerio-salud-publica', 'ministerio-economia-finanzas'."
        ),
    )
    limit: int = Field(
        DEFAULT_LIMIT,
        ge=1,
        le=MAX_LIMIT,
        description="Cantidad de noticias a devolver (se pagina si supera ~10 por página).",
    )
    pagina: int = Field(
        0,
        ge=0,
        description="Página inicial de la paginación (0-based, ~10 tarjetas por página).",
    )


class BuscarArgs(BaseModel):
    query: str = Field(
        ...,
        description="Texto a buscar (se envía como search_api_fulltext).",
    )
    limit: int = Field(
        DEFAULT_SEARCH_LIMIT,
        ge=1,
        le=MAX_SEARCH_LIMIT,
        description="Cantidad máxima de resultados de noticias a devolver.",
    )
    subsite: str | None = Field(
        None,
        description=(
            "Si se indica, busca dentro de /{subsite}/buscar en vez del buscador "
            "general de todo gub.uy (ej. 'presidencia')."
        ),
    )
