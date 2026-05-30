"""Readable resources for the ANEP education module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import BASE_URL, MODULE


@resource(
    uri="uru://educacion/guia-de-uso",
    name="Guía de uso de los datos educativos de ANEP",
    description="Cómo buscar y consultar los datos abiertos de ANEP (vía CKAN).",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_de_uso() -> str:
    return (
        "# Guía de uso de los datos educativos de ANEP\n\n"
        "Los datos de ANEP (Administración Nacional de Educación Pública) se "
        f"publican en el Catálogo Nacional de Datos Abiertos ({BASE_URL}), "
        "bajo la organización `anep`.\n\n"
        "## Flujo recomendado\n\n"
        "1. **Buscar datasets** de ANEP con `educacion_buscar` (búsqueda fijada "
        "a la organización ANEP; parámetro opcional `q`).\n"
        "2. **Ver el detalle** de un dataset con `educacion_get_dataset` (por "
        "slug o id) para listar sus recursos y saber cuáles son consultables.\n"
        "3. **Consultar centros educativos** con `educacion_centros` "
        "(filtros: `departamento`, `localidad`, `q`, `subsistema`).\n\n"
        "## Datasets disponibles (solo 2)\n\n"
        "- `anep-centros-anep`: un único recurso Shapefile (RAR). Su URL está "
        "caída desde 2021 y NO tiene datastore: solo metadatos/URL.\n"
        "- `anep-http-sig-anep-edu-uy-siganep-formatos` ('Oferta educativa de "
        "la ANEP'): cinco recursos XLSX. Tres tienen datastore consultable "
        "(Secundaria/DGES, Formación docente/CFE, 7°/8°/9°) y dos son solo "
        "descarga (Primaria/CEIP, UTU/CETP).\n\n"
        "## Notas\n\n"
        "- NO existe un dataset separado de 'matrícula' ni de 'resultados': la "
        "matrícula, repetición y deserción vienen como COLUMNAS dentro de las "
        "filas por centro de la 'Oferta educativa'.\n"
        "- El Geoportal de ANEP (sig.anep.edu.uy / ArcGIS) NO es una API usable "
        "y queda fuera de alcance.\n"
        "- En Secundaria (DGES) un mismo centro puede aparecer en varias filas "
        "(una por oferta); deduplicá por 'Ruee Calculado' o 'Nombre' si "
        "necesitás un registro por centro.\n"
    )
