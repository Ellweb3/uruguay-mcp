"""Readable resources for the health (salud) module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import BASE_URL, MODULE


@resource(
    uri="uru://salud/guia-de-uso",
    name="Guía de uso de los datos de salud",
    description="Cómo descubrir y consultar datos de salud del portal CKAN nacional.",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_de_uso() -> str:
    return (
        "# Guía de uso de los datos de salud\n\n"
        f"Todos los datos de salud provienen del Catálogo Nacional de Datos "
        f"Abiertos (portal CKAN de AGESIC, {BASE_URL}). No requiere clave.\n\n"
        "## Flujo recomendado\n\n"
        "1. **Buscar datasets** con `salud_buscar` (parámetro `q`). Por defecto "
        "descubre por el grupo `salud` (276 datasets: MSP, FNR, ASSE, "
        "intendencias…). Filtro opcional `org`: `msp` o "
        "`fondo-nacional-de-recursos`.\n"
        "2. **Ver el detalle** de un dataset con `salud_get_dataset` (id o slug) "
        "para listar sus recursos y cuáles tienen `datastore_active`.\n"
        "3. **Policlínicas**: `salud_policlinicas` resuelve el dataset "
        "`ubicacion-de-policlinicas` (Montevideo). Su CSV NO tiene datastore "
        "activo; con `download=true` descarga y parsea las filas.\n"
        "4. **Medicamentos**: `salud_medicamentos` consulta el gasto por "
        "tratamientos con medicamentos del FNR (filtros `q`, `anio`, `area`, o "
        "`sql` para agregación).\n"
        "5. **Consulta genérica**: `salud_datastore_query` ejecuta "
        "`datastore_search` (o `datastore_search_sql` si se pasa `sql`) sobre "
        "cualquier `resource_id` con datastore activo (vacunación, egresos, "
        "ELEPEM, solicitudes/actos del FNR, etc.).\n\n"
        "## Notas\n\n"
        "- No existe un 'Formulario Terapéutico de Medicamentos' en este "
        "catálogo; vive en el sitio del MSP (gub.uy/ministerio-salud-publica).\n"
        "- Solo los recursos con `datastore_active: true` admiten "
        "`datastore_search`/`datastore_search_sql`.\n"
        "- En `sql` la tabla es el `resource_id` entre comillas dobles y las "
        'columnas también (case-sensitive, ej. `"Area_prestacion"`). Debe ser '
        "una única sentencia SELECT, sin ';' intermedios ni DDL/DML.\n"
    )


@resource(
    uri="uru://salud/fuentes",
    name="Fuentes principales de datos de salud",
    description="Organizaciones y datasets clave del grupo salud en el catálogo nacional.",
    module=MODULE,
    mime_type="text/markdown",
)
def fuentes() -> str:
    return (
        "# Fuentes principales de datos de salud\n\n"
        "El grupo `salud` del Catálogo Nacional de Datos Abiertos reúne datos de "
        "múltiples organismos. Para el listado exacto y actualizado usá "
        "`salud_buscar`.\n\n"
        "## Organizaciones\n\n"
        "- **MSP** (`msp`) — Ministerio de Salud Pública (vacunación, egresos, "
        "ELEPEM, etc.).\n"
        "- **FNR** (`fondo-nacional-de-recursos`) — Fondo Nacional de Recursos: "
        "gasto por tratamientos con medicamentos, solicitudes de trámites "
        "autorizados, actos médicos.\n"
        "- **Intendencias / ASSE** — p. ej. ubicación de policlínicas "
        "(intendencia de Montevideo).\n\n"
        "## Datasets de referencia\n\n"
        "- `ubicacion-de-policlinicas` — ubicación de policlínicas (CSV, sin "
        "datastore activo: usar `salud_policlinicas`).\n"
        "- `fondo-nacional-de-recursos-gasto-por-tratamientos-fondo-nacional-de-recursos` "
        "— gasto por tratamientos con medicamentos del FNR (CSV por año, con "
        "datastore activo: usar `salud_medicamentos`).\n"
    )
