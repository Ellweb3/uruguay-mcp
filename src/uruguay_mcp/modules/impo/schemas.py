"""Pydantic argument models for IMPO tools.

Estos modelos definen el JSON schema que ``discover_tools`` expone al modelo,
así que las descripciones (en español) son la interfaz advertida.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .constants import MAX_ARTICULOS, MAX_FEED_ITEMS


class GetNormaArgs(BaseModel):
    tipo: Literal["ley", "decreto", "constitucion"] = Field(
        ...,
        description="Tipo de norma: 'ley', 'decreto' o 'constitucion'.",
    )
    numero: str | None = Field(
        None,
        description=(
            "Número de la norma (ej. '18331'). Requerido para ley y decreto; "
            "se ignora para constitucion."
        ),
    )
    anio: int = Field(
        ...,
        ge=1800,
        le=2100,
        description=(
            "Año de 4 dígitos (OBLIGATORIO completo, ej. 2008 o 1991). "
            "Los decretos exigen el año completo (500-1991, no 500-91)."
        ),
    )
    version: Literal["consolidada", "original"] = Field(
        "consolidada",
        description=(
            "'consolidada' = texto actualizado (por defecto); 'original' = "
            "texto tal como se publicó. 'original' sólo aplica a ley y decreto."
        ),
    )
    max_articulos: int = Field(
        MAX_ARTICULOS,
        ge=1,
        le=MAX_ARTICULOS,
        description="Cantidad máxima de artículos a devolver.",
    )


class DiarioOficialArgs(BaseModel):
    fecha: str | None = Field(
        None,
        description=(
            "Fecha del Diario Oficial en formato 'YYYY-MM-DD' o 'DD/MM/YYYY'. "
            "Por defecto: hoy."
        ),
    )
    seccion: Literal["indice", "documentos", "avisos", "um", "all"] = Field(
        "all",
        description=(
            "Sección: 'indice', 'documentos', 'avisos', 'um' (último momento) "
            "o 'all' (todas). Por defecto 'all'."
        ),
    )


class BuscarNormativaArgs(BaseModel):
    query: str = Field(
        "",
        description="Texto libre a buscar (ej. 'protección de datos personales').",
    )
    tipo: Literal["ley", "decreto", "constitucion"] | None = Field(
        None,
        description="Tipo opcional para resolver directo a la norma (ley/decreto/constitucion).",
    )
    numero: str | None = Field(
        None, description="Número de norma opcional (para atajo a la norma directa)."
    )
    anio: int | None = Field(
        None,
        ge=1800,
        le=2100,
        description="Año de 4 dígitos opcional (para atajo a la norma directa).",
    )


class BuscarTextoArgs(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description=(
            "Texto a buscar en el sitio de IMPO (ej. 'datos personales'). "
            "Búsqueda full-text real vía el feed RSS de WordPress."
        ),
    )
    pagina: int = Field(
        1,
        ge=1,
        le=100,
        description="Página de resultados (1-based, 10 resultados por página).",
    )
    max_resultados: int = Field(
        MAX_FEED_ITEMS,
        ge=1,
        le=MAX_FEED_ITEMS,
        description="Cantidad máxima de resultados a devolver (tope 10).",
    )


class NovedadesArgs(BaseModel):
    max_resultados: int = Field(
        MAX_FEED_ITEMS,
        ge=1,
        le=MAX_FEED_ITEMS,
        description="Cantidad máxima de ítems a devolver (el feed trae ~10).",
    )
    categoria: str | None = Field(
        None,
        description=(
            "Filtro opcional (cliente) por categoría del ítem, ej. "
            "'Publicaciones Jurídicas' o 'Novedades editoriales'."
        ),
    )


class ReferenciasNormaArgs(BaseModel):
    tipo: Literal["ley", "decreto", "constitucion"] = Field(
        ...,
        description="Tipo de norma: 'ley', 'decreto' o 'constitucion'.",
    )
    anio: int = Field(
        ...,
        ge=1800,
        le=2100,
        description="Año de 4 dígitos (OBLIGATORIO completo, ej. 2008).",
    )
    numero: str | None = Field(
        None,
        description=(
            "Número de la norma (ej. '18331'). Requerido para ley y decreto; "
            "se ignora para constitucion."
        ),
    )
    version: Literal["consolidada", "original"] = Field(
        "consolidada",
        description=(
            "'consolidada' = texto actualizado (por defecto); 'original' = "
            "texto tal como se publicó. 'original' sólo aplica a ley y decreto."
        ),
    )
