"""Readable resources for the ACCE (compras estatales) module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import MODULE, OCDS_BASE_URL


@resource(
    uri="uru://acce/guia-de-uso",
    name="Guía de uso de datos de compras estatales (ACCE)",
    description="Cómo consultar contrataciones públicas OCDS y datasets de ACCE.",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_de_uso() -> str:
    return (
        "# Guía de uso de datos de compras estatales (ACCE)\n\n"
        f"Datos de contrataciones públicas del Estado uruguayo, publicados como "
        f"OCDS 1.1 en {OCDS_BASE_URL} y como datasets abiertos en el catálogo "
        "nacional (CKAN).\n\n"
        "## Flujo recomendado\n\n"
        "1. **Listar compras recientes** con `acce_recientes` (feed OCDS). "
        "Devuelve, por evento, id_compra, release_id, tag, título y fecha. "
        "Opcional: filtrar por año/mes o por tag.\n"
        "2. **Ver las etapas de una compra** con `acce_get_compra` (id_compra): "
        "lista los eventos enlazados (release_id + tag). Nota: el record no "
        "incluye el detalle, solo los enlaces.\n"
        "3. **Ver el detalle de un evento** con `acce_get_release` (release_id): "
        "datos del llamado (tender) o de la adjudicación (award).\n"
        "4. **Buscar datasets de ACCE** (RUPE, históricos) con `acce_buscar`.\n\n"
        "## Notas\n\n"
        "- Las API son públicas y de solo lectura; no requieren clave.\n"
        "- En los llamados, `tender.value` suele venir nulo; en las "
        "adjudicaciones, el valor del award a menudo no se publica.\n"
        "- El tag de cada evento puede ser: tender, award, tenderUpdate, "
        "tenderAmendment, awardUpdate.\n"
    )


@resource(
    uri="uru://acce/glosario-ocds",
    name="Glosario OCDS para compras estatales",
    description="Términos del estándar OCDS usados en los datos de ACCE.",
    module=MODULE,
    mime_type="text/markdown",
)
def glosario_ocds() -> str:
    return (
        "# Glosario OCDS para compras estatales\n\n"
        "Términos del estándar Open Contracting Data Standard (OCDS 1.1) tal "
        "como aparecen en los datos de ACCE.\n\n"
        "- **id_compra**: identificador numérico de la compra (procurement). "
        "Es el parámetro de `acce_get_compra`.\n"
        "- **release_id**: identificador de un evento/etapa concreto (ej. "
        "`llamado-1343954`, `adjudicacion-1342977`). Es el parámetro de "
        "`acce_get_release`.\n"
        "- **ocid**: identificador OCDS de la compra (`ocds-yfs5dr-<id_compra>`).\n"
        "- **tender**: etapa de llamado/licitación (objeto, organismo, ítems, "
        "plazos, método).\n"
        "- **award**: adjudicación (proveedor adjudicatario, ítems, valor).\n"
        "- **tag**: tipo de evento (tender, award, tenderUpdate, "
        "tenderAmendment, awardUpdate).\n"
        "- **procurementMethodDetails**: tipo de procedimiento, ej. "
        "'Licitación Abreviada'.\n"
    )
