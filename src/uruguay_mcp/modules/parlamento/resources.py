"""Readable resources for the Parlamento del Uruguay module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import CKAN_BASE_URL, MODULE, ORG_SLUG


@resource(
    uri="uru://parlamento/guia-de-uso",
    name="Guía de uso de los datos del Parlamento del Uruguay",
    description="Cómo buscar y consultar los datos abiertos del Parlamento.",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_de_uso() -> str:
    return (
        "# Datos abiertos del Parlamento del Uruguay\n\n"
        f"Datasets publicados por la organización `{ORG_SLUG}` en el Catálogo "
        f"Nacional de Datos Abiertos (CKAN de AGESIC, {CKAN_BASE_URL}). Cubren la "
        "Cámara de Representantes (Diputados) y la Cámara de Senadores.\n\n"
        "## Flujo recomendado\n\n"
        "1. **Buscar datasets** por tema con `parlamento_buscar` (el filtro de "
        "organización se inyecta automáticamente).\n"
        "2. **Ver el detalle** de un dataset con `parlamento_get_dataset` (por "
        "slug o uuid): obtenés los recursos, divididos por legislatura, con su "
        "`resource_id`, formato y `datastore_active`.\n"
        "3. **Asistencias** a sesiones con `parlamento_asistencias` "
        "(cámara + legislatura).\n"
        "4. **Actividades/citaciones** (plenarios y comisiones) con "
        "`parlamento_actividades`.\n\n"
        "## Notas importantes\n\n"
        "- La API CKAN es pública y de solo lectura; no requiere clave.\n"
        "- Los recursos están divididos **por legislatura** (50, 49, 48, ...). "
        "Solo los recursos con `datastore_active: true` admiten consulta de "
        "filas; las convenience tools eligen la legislatura más reciente "
        "consultable si no se especifica.\n"
        "- **Mismatch de datos**: la copia CKAN de asistencias expone filas a "
        "nivel sesión (Fecha, Asunto, Carpetas, Título), NO el presentismo por "
        "legislador (Nombre, Citaciones, Asistencias %). Para asistencia "
        "individual hay que ir a la fuente directa de parlamento.gub.uy.\n"
    )


@resource(
    uri="uru://parlamento/legislaturas",
    name="Legislaturas del Parlamento del Uruguay",
    description="Referencia de legislaturas y sus periodos.",
    module=MODULE,
    mime_type="text/markdown",
)
def legislaturas() -> str:
    return (
        "# Legislaturas del Parlamento del Uruguay\n\n"
        "Cada legislatura dura cinco años y suele corresponder a un recurso "
        "separado dentro de cada dataset. Periodos recientes:\n\n"
        "- **50ª**: 2025-2030\n"
        "- **49ª**: 2020-2025\n"
        "- **48ª**: 2015-2020\n"
        "- **47ª**: 2010-2015\n"
        "- **46ª**: 2005-2010\n"
        "- **45ª**: 2000-2005\n\n"
        "No todas las legislaturas tienen `datastore_active: true`; usá "
        "`parlamento_get_dataset` para ver qué recursos se pueden consultar.\n"
    )
