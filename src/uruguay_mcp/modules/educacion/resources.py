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


@resource(
    uri="uru://educacion/subsistemas",
    name="Subsistemas educativos de ANEP",
    description="Códigos de subsistema y cuáles tienen datastore consultable en educacion_centros.",
    module=MODULE,
    mime_type="text/markdown",
)
def subsistemas() -> str:
    return (
        "# Subsistemas educativos de ANEP\n\n"
        "Códigos para usar con el parámetro `subsistema` de `educacion_centros`.\n\n"
        "## Con datastore consultable (búsqueda directa)\n\n"
        "- `ces` — Secundaria / DGES (Consejo de Educación Secundaria). "
        "Es el subsistema por defecto cuando no se indica ninguno.\n"
        "- `cfe` — Formación docente / CFE (Consejo de Formación en Educación).\n"
        "- `789` — 7°, 8° y 9° grado en escuelas rurales (tabla pequeña, ~55 filas).\n\n"
        "## Solo descarga (sin datastore)\n\n"
        "Para estos dos, `educacion_centros` devuelve la URL del XLSX en lugar de "
        "filas, porque no tienen datastore activo en el portal CKAN:\n\n"
        "- `ceip` — Primaria / CEIP (Consejo de Educación Inicial y Primaria).\n"
        "- `cetp` — UTU / CETP (Consejo de Educación Técnico-Profesional).\n\n"
        "## Cómo explorar la oferta\n\n"
        "Usá `educacion_centros` con el parámetro `subsistema` para filtrar por "
        "sistema educativo, y combinalo con `departamento` o `localidad` para "
        "acotar geográficamente. Para ver todos los recursos disponibles del "
        "dataset usá `educacion_get_dataset` con el id "
        "`anep-http-sig-anep-edu-uy-siganep-formatos`.\n"
    )
