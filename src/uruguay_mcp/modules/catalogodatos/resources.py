"""Readable resources for the national open-data catalog (CKAN) module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import BASE_URL, MODULE


@resource(
    uri="uru://catalogodatos/guia-de-uso",
    name="Guía de uso del Catálogo Nacional de Datos Abiertos",
    description="Cómo buscar y consultar datos del portal CKAN de AGESIC.",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_de_uso() -> str:
    return (
        "# Guía de uso del Catálogo Nacional de Datos Abiertos\n\n"
        f"Portal CKAN de AGESIC ({BASE_URL}) con datasets del Estado uruguayo.\n\n"
        "## Flujo recomendado\n\n"
        "1. **Buscar datasets** por tema con `catalogo_search_datasets` "
        "(filtros: organization, group, tags).\n"
        "2. **Ver el detalle** de un dataset con `catalogo_get_dataset` "
        "(por id o slug) para obtener sus recursos.\n"
        "3. **Listar organizaciones** publicadoras con "
        "`catalogo_list_organizations`.\n"
        "4. **Listar categorías/grupos** temáticos con `catalogo_list_groups`.\n"
        "5. **Consultar datos tabulares** de un recurso con datastore activo "
        "usando `catalogo_query_datastore` (resource_id).\n"
        "6. **Inspeccionar un recurso** (formato, tamaño, datastore_active) con "
        "`catalogo_resource_show` (resource_id).\n"
        "7. **Consultar con SQL** un recurso con datastore activo usando "
        "`catalogo_datastore_sql` (una sola sentencia SELECT).\n"
        "8. **Listar etiquetas** del portal con `catalogo_list_tags` "
        "(filtro opcional por texto).\n"
        "9. **Ver novedades** (datasets modificados recientemente) con "
        "`catalogo_recent_datasets`.\n\n"
        "## Notas\n\n"
        "- La API CKAN es pública y de solo lectura; no requiere clave.\n"
        "- Solo los recursos con `datastore_active: true` admiten "
        "`catalogo_query_datastore` y `catalogo_datastore_sql`.\n"
        "- En `catalogo_datastore_sql` la tabla es el `resource_id` entre "
        'comillas dobles: `SELECT * FROM "<resource_id>" LIMIT 50`. Debe ser una '
        "única sentencia SELECT, sin ';' intermedios, comentarios ni DDL/DML "
        "(el WAF del portal rechaza el resto). Los registros incluyen columnas "
        "internas `_id` y `_full_text`.\n"
    )


@resource(
    uri="uru://catalogodatos/categorias",
    name="Categorías temáticas del catálogo",
    description="Listado orientativo de grupos/categorías del portal CKAN.",
    module=MODULE,
    mime_type="text/markdown",
)
def categorias() -> str:
    return (
        "# Categorías temáticas del catálogo\n\n"
        "Grupos habituales del Catálogo Nacional de Datos Abiertos. Para el "
        "listado exacto y actualizado con su cantidad de datasets, usá la "
        "herramienta `catalogo_list_groups`.\n\n"
        "- Salud\n"
        "- Educación\n"
        "- Transporte y movilidad\n"
        "- Medio ambiente\n"
        "- Economía y finanzas\n"
        "- Población y sociedad\n"
        "- Gobierno y transparencia\n"
        "- Seguridad\n"
        "- Justicia\n"
        "- Territorio y geografía\n"
    )
