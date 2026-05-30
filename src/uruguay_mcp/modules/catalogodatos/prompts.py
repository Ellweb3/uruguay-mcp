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


@prompt(
    name="catalogo_sql_consulta",
    module=MODULE,
    description="Instrucción para ejecutar una consulta SQL sobre el datastore de un recurso.",
)
def catalogo_sql_consulta(resource_id: str, objetivo: str | None = None) -> str:
    meta = (
        f" El objetivo es: {objetivo}."
        if objetivo
        else ""
    )
    return (
        f"Primero verificá con catalogo_resource_show que el recurso '{resource_id}' "
        "tenga datastore_active en true. Luego ejecutá una consulta SQL de solo "
        "lectura con catalogo_datastore_sql. La tabla es el resource_id entre "
        f'comillas dobles, por ejemplo: SELECT * FROM "{resource_id}" LIMIT 50.'
        f"{meta} Usá una única sentencia SELECT (sin ';' intermedios, sin "
        "comentarios y sin DDL/DML). Recordá que los registros incluyen columnas "
        "internas de CKAN como _id y _full_text."
    )
