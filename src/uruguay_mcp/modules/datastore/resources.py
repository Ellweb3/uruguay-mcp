"""Readable resources for the cross-source local datastore module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import MAX_RESULT_ROWS, MAX_ROWS, MODULE


@resource(
    uri="uru://datastore/guia-uso",
    name="Guía de uso del datastore local",
    description="Cómo cargar fuentes y hacer consultas/JOINs SQL en el datastore local.",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_uso() -> str:
    return (
        "# Datastore local (SQL cruzado entre fuentes)\n\n"
        "Este módulo permite combinar datos de distintas APIs en una base SQLite "
        "local y consultarlos con SQL de sólo lectura.\n\n"
        "## Flujo típico\n\n"
        "1. **Cargar fuentes** en tablas:\n"
        "   - `datastore_load_csv(url, table)` — descarga un CSV y lo importa.\n"
        "   - `datastore_load_ckan_resource(resource_id, table, base)` — importa un "
        "recurso CKAN (por defecto del Catálogo Nacional).\n"
        "2. **Inspeccionar** lo cargado con `datastore_list_tables` (nombres de "
        "tablas, columnas y cantidad de filas).\n"
        "3. **Consultar** con `datastore_sql(query)` usando una única sentencia "
        "`SELECT` (se admiten `JOIN`, `WHERE`, `GROUP BY`, etc.).\n\n"
        "## Reglas y límites\n\n"
        "- Sólo se permite **una sentencia SELECT**. Se rechaza cualquier otra cosa "
        "(`INSERT`, `UPDATE`, `DELETE`, `DROP`, `PRAGMA`, `ATTACH`, varias "
        "sentencias, etc.).\n"
        "- Los nombres de tabla se **sanitizan** (sólo letras, números y guion bajo).\n"
        f"- Cada carga importa hasta **{MAX_ROWS:,} filas**.\n"
        f"- Cada consulta devuelve hasta **{MAX_RESULT_ROWS:,} filas** "
        "(`truncated=true` si hay más).\n"
        "- Todas las columnas se guardan como **TEXT**; usá `CAST(col AS REAL)` o "
        "`CAST(col AS INTEGER)` para comparaciones numéricas.\n\n"
        "## Ejemplo de JOIN\n\n"
        "```sql\n"
        "SELECT a.depto, a.poblacion, b.presupuesto\n"
        "FROM censo a JOIN gasto b ON a.depto = b.depto\n"
        "ORDER BY CAST(b.presupuesto AS REAL) DESC\n"
        "```\n"
    )
