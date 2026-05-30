"""Pydantic argument models for ACCE tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import DEFAULT_FEED_LIMIT, DEFAULT_ROWS, MAX_FEED_LIMIT, MAX_ROWS


class RecientesArgs(BaseModel):
    year: int | None = Field(
        None, ge=2000, le=2100, description="Año del feed mensual (ej. 2026)."
    )
    month: int | None = Field(
        None, ge=1, le=12, description="Mes del feed (1-12). Requiere también 'year'."
    )
    tag: str | None = Field(
        None,
        description=(
            "Filtrar por categoría OCDS: tender, award, tenderUpdate, "
            "tenderAmendment, awardUpdate."
        ),
    )
    limit: int = Field(
        DEFAULT_FEED_LIMIT,
        ge=1,
        le=MAX_FEED_LIMIT,
        description="Cantidad máxima de eventos a devolver.",
    )


class CompraArgs(BaseModel):
    idcompra: str = Field(
        ..., description="ID numérico de la compra (id_compra), ej. '1343954'."
    )


class ReleaseArgs(BaseModel):
    param: str = Field(
        ...,
        description=(
            "release_id / guid del evento OCDS, ej. 'llamado-1343954', "
            "'adjudicacion-1342977', 'ajuste_llamado-45347'."
        ),
    )


class BuscarArgs(BaseModel):
    query: str = Field("", description="Texto de búsqueda libre (ej. 'rupe', 'proveedores').")
    rows: int = Field(DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de resultados.")
    start: int = Field(0, ge=0, description="Desplazamiento para paginación.")
