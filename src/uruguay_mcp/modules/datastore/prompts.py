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


@prompt(
    name="datastore_cargar_ckan",
    module=MODULE,
    description="Instrucción para cargar un recurso CKAN e inspeccionar y consultar su tabla.",
)
def datastore_cargar_ckan(resource_id: str, tabla: str = "recurso") -> str:
    return (
        f"Cargá el recurso CKAN con id '{resource_id}' en una tabla local llamada "
        f"'{tabla}' usando datastore_load_ckan_resource (parámetros resource_id y table). "
        "Una vez cargado, inspeccioná el esquema y la cantidad de filas con "
        "datastore_list_tables. Luego ejecutá una consulta exploratoria con "
        "datastore_sql (por ejemplo SELECT * FROM "
        f"{tabla} LIMIT 10) para mostrar una muestra de los datos. "
        "Recordá que todos los valores se almacenan como TEXT; usá CAST(...) para "
        "comparaciones numéricas."
    )


@prompt(
    name="datastore_agregar_por_columna",
    module=MODULE,
    description="Instrucción para agrupar y agregar filas de una tabla cargada por una columna.",
)
def datastore_agregar_por_columna(
    tabla: str,
    columna: str,
    metrica: str = "*",
) -> str:
    return (
        f"Agrupá los datos de la tabla '{tabla}' por la columna '{columna}' usando "
        "datastore_sql. Primero verificá que la tabla existe con datastore_list_tables. "
        f"Luego ejecutá: SELECT {columna}, COUNT({metrica}) AS total "
        f"FROM {tabla} GROUP BY {columna} ORDER BY total DESC. "
        "Si necesitás sumar o promediar un campo numérico en lugar de contar, usá "
        "SUM(CAST(campo AS REAL)) o AVG(CAST(campo AS REAL)) porque los valores "
        "están almacenados como TEXT."
    )
