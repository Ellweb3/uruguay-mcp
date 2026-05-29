"""Reusable prompts for the cross-source local datastore module."""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="datastore_unir_dos_fuentes",
    module=MODULE,
    description="Instrucción para unir (JOIN) datos de dos fuentes distintas localmente.",
)
def datastore_unir_dos_fuentes(
    fuente_a: str,
    fuente_b: str,
    clave: str = "id",
) -> str:
    return (
        "Quiero cruzar datos de dos fuentes distintas usando el datastore local. "
        f"Primero cargá la fuente '{fuente_a}' en una tabla (con datastore_load_csv "
        "o datastore_load_ckan_resource) y la fuente "
        f"'{fuente_b}' en otra tabla. Verificá el esquema con datastore_list_tables. "
        f"Luego unílas con datastore_sql usando un JOIN por la columna '{clave}' "
        "(o la que corresponda) y devolvé las filas combinadas. Recordá que sólo se "
        "permiten sentencias SELECT."
    )


@prompt(
    name="datastore_consulta_sql",
    module=MODULE,
    description="Instrucción para analizar las tablas cargadas con una consulta SELECT.",
)
def datastore_consulta_sql(objetivo: str) -> str:
    return (
        f"Objetivo: {objetivo}. Primero listá las tablas disponibles con "
        "datastore_list_tables para conocer nombres de tablas y columnas. Después "
        "escribí una única consulta SELECT (de sólo lectura) y ejecutala con "
        "datastore_sql. Como los valores se guardan como TEXT, usá CAST(...) cuando "
        "necesites comparaciones numéricas o de fecha."
    )
