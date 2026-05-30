"""Modelos de argumentos (Pydantic) para las herramientas de INUMET.

Estos modelos son además el esquema JSON que ``discover_tools`` publica al
modelo, así que las descripciones (en español) son la interfaz pública.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import MAX_DIAS_PRONOSTICO, MAX_ESTACIONES


class EstacionesArgs(BaseModel):
    station: str | None = Field(
        None,
        description=(
            "Filtro opcional: subcadena del nombre (displayNamePublic) o "
            "identificador (idStr/id) de la estación. Sin filtro devuelve todas."
        ),
    )
    automatic_only: bool = Field(
        True,
        description=(
            "Si es true (por defecto) devuelve solo estaciones automáticas "
            "(tipoAutomatica=true)."
        ),
    )
    limit: int = Field(
        MAX_ESTACIONES,
        ge=1,
        le=MAX_ESTACIONES,
        description="Cantidad máxima de estaciones a devolver.",
    )


class PronosticoArgs(BaseModel):
    days: int = Field(
        MAX_DIAS_PRONOSTICO,
        ge=1,
        le=MAX_DIAS_PRONOSTICO,
        description="Cantidad máxima de días del pronóstico a devolver (~4 disponibles).",
    )


class AlertasArgs(BaseModel):
    """Las alertas no requieren parámetros (se consulta la página /alerta)."""
