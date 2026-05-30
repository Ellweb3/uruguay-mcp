"""Readable MCP resources for the INE statistical catalog module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import MODULE


@resource(
    uri="uru://ine/guia-fuentes",
    name="Guía de fuentes estadísticas del INE",
    description=(
        "Panorama de las principales fuentes del INE (ECH, censos, IPC y otras) "
        "y cómo localizarlas con las herramientas del módulo."
    ),
    module=MODULE,
    mime_type="text/markdown",
)
def guia_fuentes() -> str:
    return (
        "# Fuentes estadísticas del INE\n\n"
        "El catálogo ANDA del INE es el *Inventario de Operaciones Estadísticas "
        "del Sistema Estadístico Nacional* (~389 estudios de INE, BCU, OSE, MGAP, "
        "INC y otros organismos).\n\n"
        "## Principales fuentes\n\n"
        "- **ECH** — Encuesta Continua de Hogares. Empleo, ingresos y pobreza; "
        "base anual de microdatos.\n"
        "- **Censos de Población y Vivienda** — Conteo poblacional (último 2023).\n"
        "- **IPC** — Índice de Precios al Consumo, mensual.\n"
        "- **ECVU / encuestas temáticas** — Condiciones de vida y módulos "
        "específicos.\n"
        "- **Cuentas y estadísticas económicas** — Operaciones de organismos "
        "como BCU y MGAP incluidas en el inventario.\n\n"
        "## Cómo encontrarlas\n\n"
        "1. `ine_search_studies` — buscá por tema (p.ej. 'hogares', 'precios', "
        "'censo'); anotá el `idno` (string `URY-...-vNN`).\n"
        "2. `ine_get_study` — pasá el `idno` para obtener metadatos completos, "
        "acceso a datos y enlaces de descarga.\n"
        "3. `ine_list_ckan_datasets` — fallback para recursos tabulares "
        "(CSV/Excel) del INE en el Catálogo Nacional (CKAN, organization=ine).\n"
    )


@resource(
    uri="uru://ine/idno-convencion",
    name="Convención de identificadores idno del INE",
    description=(
        "Explica el formato del idno ANDA y por qué se usa en lugar del id "
        "numérico para consultar el detalle de un estudio."
    ),
    module=MODULE,
    mime_type="text/markdown",
)
def idno_convencion() -> str:
    return (
        "# Identificadores idno del catálogo ANDA\n\n"
        "Cada estudio tiene un `idno` con forma `URY-<ORGANISMO>-<OPERACION>-"
        "<AÑO>-vNN`, por ejemplo `URY-INE-ECH-2023-v01`.\n\n"
        "- `URY` — país (Uruguay).\n"
        "- `<ORGANISMO>` — entidad responsable (INE, BCU, OSE, ...).\n"
        "- `<OPERACION>` — sigla de la operación (ECH, IPC, ...).\n"
        "- `<AÑO>` — año de referencia.\n"
        "- `vNN` — número de versión.\n\n"
        "## Importante\n\n"
        "Para pedir el detalle de un estudio con `ine_get_study` se usa el "
        "`idno` (string), **no** el `id` numérico. Obtené el `idno` desde los "
        "resultados de `ine_search_studies`.\n"
    )


@resource(
    uri="uru://ine/datastore-flujo",
    name="Flujo DataStore del INE (descubrir y consultar)",
    description=(
        "Explica cómo descubrir recursos consultables del INE en CKAN y consultar "
        "sus filas sin hardcodear ids."
    ),
    module=MODULE,
    mime_type="text/markdown",
)
def datastore_flujo() -> str:
    return (
        "# Consultar datos del INE vía CKAN DataStore\n\n"
        "Algunos recursos del INE en el Catálogo Nacional (CKAN, "
        "organization=ine) tienen **DataStore activo**, lo que permite consultarlos "
        "por filas sin descargar el archivo completo. Los `resource_id` pueden "
        "rotar, así que **siempre se descubren en tiempo de ejecución** — nunca se "
        "hardcodean.\n\n"
        "## Flujo recomendado\n\n"
        "1. `ine_find_data_resources` — pasá un `theme` (p.ej. 'precios', "
        "'empleo'); devuelve SOLO los recursos con `datastore_active=true`, con su "
        "`id`, `name`, `format` y el dataset al que pertenecen.\n"
        "2. `ine_datastore_fields` — pasá el `resource_id` para ver el esquema de "
        "columnas (id y tipo) de forma barata, antes de traer filas.\n"
        "3. `ine_datastore_query` — pasá el `resource_id` (más `limit`, `offset` o "
        "`q`) para obtener `fields`, `total` y `records`.\n\n"
        "## Detalle de un dataset\n\n"
        "`ine_dataset_resources` recibe el `dataset_name` (slug) y lista todos sus "
        "recursos, marcando cuáles son consultables (`queryable_resources`) y "
        "cuáles solo se descargan.\n\n"
        "## Nota\n\n"
        "Si un recurso no está en el DataStore, `ine_datastore_query` devolverá un "
        "error claro: usá `ine_find_data_resources` para localizar uno consultable.\n"
    )
