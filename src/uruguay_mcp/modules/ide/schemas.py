"""Pydantic argument models for IDE Uruguay tools.

These double as the JSON schema advertised to the model by ``discover_tools``,
so field descriptions matter — keep them clear and Spanish-friendly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .constants import DEFAULT_COUNT, DEFAULT_LIMIT, MAX_COUNT, MAX_LIMIT


class ListarCapasArgs(BaseModel):
    filtro: str | None = Field(
        None,
        description=(
            "Subcadena para filtrar las capas por nombre o workspace "
            "(ej. 'catastro', 'limite', 'depart', 'calle')."
        ),
    )
    incluir_titulos: bool = Field(
        False,
        description="Incluir los títulos legibles de cada capa (más verboso).",
    )


class FeaturesArgs(BaseModel):
    capa: str = Field(
        ...,
        description=(
            "Nombre de la capa WFS (typeNames con prefijo de workspace, ej. "
            "'ws_catastro:departamentos' o 'ET_CATASTRO:parcelario_urbano')."
        ),
    )
    bbox: str | None = Field(
        None,
        description=(
            "Caja envolvente en EPSG:4326 como 'miny,minx,maxy,maxx' "
            "(lat_min,lon_min,lat_max,lon_max). Se ensambla con la URI de CRS "
            "para evitar ambigüedad de ejes."
        ),
    )
    cql_filter: str | None = Field(
        None,
        description=(
            "Filtro CQL del lado del servidor, ej. \"depto='MONTEVIDEO'\" o "
            "\"depto='ROCHA' AND padron=842\". Requerido si no se pasa bbox para "
            "capas grandes."
        ),
    )
    count: int = Field(
        DEFAULT_COUNT, ge=1, le=MAX_COUNT, description="Máximo de features a devolver."
    )
    propiedades: str | None = Field(
        None,
        description="Subconjunto de atributos a devolver (propertyName, separados por coma).",
    )
    slim: bool = Field(
        True,
        description=(
            "Si true (por defecto), no devuelve las coordenadas completas: solo "
            "tipo de geometría, bbox y centroide más las propiedades. Si false, "
            "devuelve la geometría completa."
        ),
    )
    solo_conteo: bool = Field(
        False,
        description="Si true, usa resultType=hits y devuelve solo numberMatched (conteo barato).",
    )


class ParcelaCatastralArgs(BaseModel):
    tipo: str = Field(
        "urbano",
        description="Tipo de parcelario: 'urbano' o 'rural'.",
    )
    bbox: str | None = Field(
        None,
        description="Caja envolvente EPSG:4326 'miny,minx,maxy,maxx' (lat_min,lon_min,...).",
    )
    departamento: str | None = Field(
        None,
        description="Nombre del departamento en mayúsculas (ej. 'MONTEVIDEO', 'ROCHA').",
    )
    padron: int | None = Field(
        None, description="Número de padrón (identificador de parcela)."
    )
    cql_filter: str | None = Field(
        None, description="Filtro CQL avanzado adicional (se combina con departamento/padron)."
    )
    count: int = Field(
        DEFAULT_COUNT, ge=1, le=MAX_COUNT, description="Máximo de parcelas a devolver."
    )
    slim: bool = Field(True, description="Recortar la geometría (ver ide_features).")


class GeocodificarArgs(BaseModel):
    direccion: str = Field(
        ...,
        description=(
            "Dirección completa, idealmente con el TIPO de vía (ej. 'AVENIDA 18 DE "
            "JULIO 1234, MONTEVIDEO'). El prefijo de tipo mejora los resultados."
        ),
    )
    limite: int = Field(
        DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Máximo de resultados."
    )
    autocompletar: bool = Field(
        False,
        description="Si true, usa /candidates (autocompletado typeahead) en vez de direcUnica.",
    )


class GeocodificarInversoArgs(BaseModel):
    latitud: float = Field(..., description="Latitud en EPSG:4326.")
    longitud: float = Field(..., description="Longitud en EPSG:4326.")
    limite: int = Field(
        3, ge=1, le=MAX_LIMIT, description="Máximo de direcciones cercanas a devolver."
    )
