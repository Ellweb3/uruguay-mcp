"""Reusable prompts for the MIDES module."""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="mides_evolucion_prestacion",
    module=MODULE,
    description="Instrucción para reconstruir la serie mensual de una prestación social.",
)
def mides_evolucion_prestacion(prestacion: str = "Tarjeta Uruguay Social") -> str:
    return (
        f"Reconstruí la evolución de la prestación '{prestacion}' del MIDES. "
        "Primero buscá el dataset-indicador con mides_buscar (parámetro query). "
        "Luego obtené sus recursos con mides_get_dataset y elegí el recurso con "
        "datastore_active en true. Finalmente leé la serie temporal mensual con "
        "mides_serie (resource_id), usando sort por año para ordenarla. Resumí "
        "los valores y la tendencia."
    )


@prompt(
    name="mides_buscar_prestaciones",
    module=MODULE,
    description="Instrucción para buscar prestaciones e indicadores del MIDES en CKAN.",
)
def mides_buscar_prestaciones(tema: str = "asignaciones familiares") -> str:
    return (
        f"Buscá datasets del MIDES sobre '{tema}' con mides_buscar (fuerza "
        "organization:mides). Para cada resultado relevante indicá título, "
        "grupos/tags y recursos disponibles. Si necesitás el detalle completo "
        "de un dataset usá mides_get_dataset (id o name), y para leer los "
        "valores numéricos usá mides_serie sobre un recurso con datastore."
    )


@prompt(
    name="mides_donde_acudir",
    module=MODULE,
    description="Instrucción para orientar sobre recursos sociales según una necesidad.",
)
def mides_donde_acudir(necesidad: str = "violencia") -> str:
    return (
        f"Orientá sobre dónde acudir ante la necesidad '{necesidad}'. Usá "
        "mides_recursos (parámetro query) para buscar programas y servicios en "
        "la Guía Nacional de Recursos Sociales. Devolvé por cada recurso su "
        "título y la URL canónica para compartir. Si la búsqueda no devuelve "
        "resultados, indicá cómo navegar la Guía manualmente."
    )
