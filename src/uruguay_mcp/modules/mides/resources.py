"""Readable resources for the MIDES module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import CKAN_ACTION_URL, GUIA_BASE_URL, MODULE


@resource(
    uri="uru://mides/guia-de-uso",
    name="Guía de uso de los datos del MIDES",
    description="Cómo buscar prestaciones, leer series mensuales y recursos sociales.",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_de_uso() -> str:
    return (
        "# Guía de uso de los datos del MIDES\n\n"
        "El MIDES (Ministerio de Desarrollo Social) publica sus datos en dos "
        "lugares: el Catálogo Nacional de Datos Abiertos (CKAN) y la Guía "
        "Nacional de Recursos Sociales.\n\n"
        "## Datos abiertos (CKAN)\n\n"
        f"Portal CKAN ({CKAN_ACTION_URL}), ~1875 datasets de MIDES.\n\n"
        "1. **Buscar datasets/indicadores** con `mides_buscar` (fuerza "
        "organization:mides).\n"
        "2. **Ver el detalle** de un dataset con `mides_get_dataset` (id o "
        "name, ej. 'mides-indicador-10053') para obtener sus recursos y saber "
        "cuáles tienen `datastore_active`.\n"
        "3. **Leer la serie temporal mensual** de un recurso con datastore "
        "activo usando `mides_serie` (resource_id, sort, limit/offset).\n\n"
        "## Notas\n\n"
        "- La API CKAN es pública y de solo lectura; no requiere clave.\n"
        "- Las prestaciones son datasets 'indicador' (mides-indicador-NNNNN): "
        "TUS=10053/10059/13521; AFAM-PE=12027/12031/10051; Asistencia a la "
        "Vejez=10063/10268. Solo hay series agregadas mensuales (no microdato).\n"
        "- Los campos de la serie están en español con acentos (ej. 'año', "
        "'Meses', 'valor'); al pasar `sort` se codifican en la URL "
        "automáticamente.\n"
        "- 'BPS' (seguro de enfermedad/desempleo, asignaciones Ley 15.084) "
        "aparece como indicadores publicados por MIDES; buscalo con "
        "`mides_buscar`.\n\n"
        "## Guía Nacional de Recursos Sociales\n\n"
        "4. **Buscar programas/servicios** por necesidad con `mides_recursos` "
        "(query + área/población opcionales). Ver `uru://mides/guia-recursos`.\n"
    )


@resource(
    uri="uru://mides/guia-recursos",
    name="Cómo usar la Guía Nacional de Recursos Sociales",
    description="Áreas, poblaciones y navegación de guiaderecursos.mides.gub.uy.",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_recursos() -> str:
    return (
        "# Guía Nacional de Recursos Sociales\n\n"
        f"Portal {GUIA_BASE_URL}: directorio de programas y servicios sociales. "
        "No expone API JSON (es un portal JSP), por eso `mides_recursos` "
        "scrapea el HTML de la búsqueda y devuelve las URLs canónicas "
        "(`https://guiaderecursos.mides.gub.uy/{id}/{slug}`), que son estables "
        "y se pueden compartir.\n\n"
        "## Filtros orientativos (pueden cambiar)\n\n"
        "**Áreas temáticas** (parámetro `area`):\n"
        "- 8 = Maltrato / violencia\n"
        "- 10 = Salud\n"
        "- 11 = Situación de calle\n"
        "- 14 = Servicios de información\n"
        "- 15 = Cuidados\n\n"
        "**Poblaciones objetivo** (parámetro `poblacion`):\n"
        "- 2 = Adolescencia\n"
        "- 3 = Juventud\n"
        "- 4 = Adultez\n"
        "- 5 = Vejez\n"
        "- 7 = Mujeres\n"
        "- 8 = Personas trans\n\n"
        "## Notas\n\n"
        "- La búsqueda devuelve ~10 resultados por página.\n"
        "- Si el HTML cambia y no se extraen recursos, `mides_recursos` "
        "degrada y devuelve la URL de entrada a la Guía.\n"
    )
