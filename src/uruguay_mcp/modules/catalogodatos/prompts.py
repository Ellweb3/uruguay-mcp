"""Reusable prompts for the national open-data catalog (CKAN) module."""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="catalogo_buscar_por_tema",
    module=MODULE,
    description="Instrucción para buscar datasets del catálogo nacional por tema.",
)
def catalogo_buscar_por_tema(tema: str, organizacion: str | None = None) -> str:
    extra = (
        f" Limitá la búsqueda a la organización '{organizacion}'."
        if organizacion
        else ""
    )
    return (
        f"Buscá datasets sobre '{tema}' en el Catálogo Nacional de Datos Abiertos "
        "usando la herramienta catalogo_search_datasets (parámetro query)."
        f"{extra} Para cada resultado relevante indicá título, organización y "
        "formatos de recursos disponibles. Si necesitás el detalle completo de un "
        "dataset, usá catalogo_get_dataset con su id o slug."
    )


@prompt(
    name="catalogo_explorar_organizaciones",
    module=MODULE,
    description="Instrucción para explorar organizaciones y categorías del catálogo.",
)
def catalogo_explorar_organizaciones() -> str:
    return (
        "Mostrá un panorama del Catálogo Nacional de Datos Abiertos. Primero listá "
        "las organizaciones publicadoras con catalogo_list_organizations y las "
        "categorías temáticas con catalogo_list_groups. Resumí cuáles concentran "
        "más datasets (campo package_count) y sugerí por dónde empezar a explorar."
    )


@prompt(
    name="catalogo_consultar_datastore",
    module=MODULE,
    description="Instrucción para consultar los registros tabulares de un recurso.",
)
def catalogo_consultar_datastore(resource_id: str, filtro: str | None = None) -> str:
    extra = (
        f" Filtrá los registros que coincidan con '{filtro}' (parámetro query)."
        if filtro
        else ""
    )
    return (
        f"Consultá los registros del recurso '{resource_id}' con la herramienta "
        "catalogo_query_datastore (el recurso debe tener datastore activo)."
        f"{extra} Mostrá los campos disponibles y una muestra de filas, y comentá "
        "el total de registros encontrados."
    )
