"""Pydantic argument models for MIDES tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import (
    DEFAULT_RECURSOS_LIMIT,
    DEFAULT_ROWS,
    DEFAULT_SERIE_LIMIT,
    MAX_RECURSOS_LIMIT,
    MAX_ROWS,
    MAX_SERIE_LIMIT,
)


class BuscarArgs(BaseModel):
    query: str = Field(
        "",
        description=(
            "Texto de búsqueda libre (ej. 'tarjeta uruguay social', "
            "'asignaciones familiares', 'asistencia a la vejez', 'ENDIS')."
        ),
    )
    rows: int = Field(DEFAULT_ROWS, ge=1, le=MAX_ROWS, description="Cantidad de resultados.")
    start: int = Field(0, ge=0, description="Desplazamiento para paginación.")


class DatasetArgs(BaseModel):
    id: str = Field(
        ...,
        description="Name o uuid del dataset (ej. 'mides-indicador-10053').",
    )


class SerieArgs(BaseModel):
    resource_id: str = Field(
        ...,
        description=(
            "UUID de un recurso con datastore activo (obtenido de "
            "mides_get_dataset)."
        ),
    )
    limit: int = Field(
        DEFAULT_SERIE_LIMIT,
        ge=1,
        le=MAX_SERIE_LIMIT,
        description="Cantidad de registros a devolver.",
    )
    offset: int = Field(0, ge=0, description="Desplazamiento para paginación.")
    sort: str | None = Field(
        None,
        description=(
            "Orden, ej. 'año desc' (los campos están en español con acentos; "
            "se codifican en la URL automáticamente)."
        ),
    )
    q: str | None = Field(None, description="Filtro de texto libre sobre los registros.")


class RecursosArgs(BaseModel):
    query: str = Field(
        ...,
        description=(
            "Texto libre de la necesidad social (ej. 'violencia', 'vejez', "
            "'discapacidad', 'situacion de calle')."
        ),
    )
    area: int | None = Field(
        None,
        description=(
            "ID de área temática (orientativo, scrapeado del portal): "
            "8=violencia, 10=salud, 11=situación de calle, 14=información, "
            "15=cuidados."
        ),
    )
    poblacion: int | None = Field(
        None,
        description=(
            "ID de población objetivo (orientativo): 2=adolescencia, "
            "3=juventud, 4=adultez, 5=vejez, 7=mujeres, 8=personas trans."
        ),
    )
    limit: int = Field(
        DEFAULT_RECURSOS_LIMIT,
        ge=1,
        le=MAX_RECURSOS_LIMIT,
        description="Cantidad máxima de recursos sociales a devolver.",
    )
