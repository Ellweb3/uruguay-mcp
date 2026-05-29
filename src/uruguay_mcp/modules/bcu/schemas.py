"""Pydantic argument models for BCU tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly. Dates are
accepted as ISO ``YYYY-MM-DD`` strings (the client parses them to ``date``).
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from .constants import GROUP_DIVISAS, USD_CODE


class ListarMonedasArgs(BaseModel):
    grupo: int = Field(
        GROUP_DIVISAS,
        description=(
            "Grupo de monedas: 2 = divisas/billetes (dólar, real, peso arg.), "
            "0 = unidades locales indexadas (UI, UR, UP)."
        ),
    )


class UltimoCierreArgs(BaseModel):
    """Sin parámetros: devuelve la fecha del último cierre publicado."""


class CotizacionesArgs(BaseModel):
    monedas: list[int] = Field(
        default_factory=lambda: [USD_CODE],
        description=(
            "Códigos numéricos de moneda (ej. 2225 = dólar billete). "
            "Lista vacía = todas las monedas del grupo."
        ),
    )
    fecha_desde: date | None = Field(
        None,
        description="Fecha inicial del rango (YYYY-MM-DD). Si se omite, usa el último cierre.",
    )
    fecha_hasta: date | None = Field(
        None,
        description="Fecha final del rango (YYYY-MM-DD). Si se omite, usa el último cierre.",
    )
    grupo: int = Field(
        GROUP_DIVISAS,
        description="Grupo de monedas (debe coincidir con los códigos). 2 = divisas, 0 = locales.",
    )


class CotizacionUsdArgs(BaseModel):
    fecha: date | None = Field(
        None,
        description="Fecha de la cotización (YYYY-MM-DD). Si se omite, usa el último cierre.",
    )
