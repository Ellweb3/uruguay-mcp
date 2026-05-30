"""Readable MCP resources for the BPS (Observatorio / BPS en Cifras) module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import MODULE


@resource(
    uri="uru://bps/catalogo-indicadores",
    name="Catálogo de indicadores del Observatorio del BPS",
    description=(
        "Panorama de las principales categorías de indicadores del BPS "
        "(prestaciones, recaudación, cotizantes) y cómo consultarlas."
    ),
    module=MODULE,
    mime_type="text/markdown",
)
def catalogo_indicadores() -> str:
    return (
        "# Indicadores del Observatorio del BPS (BPS en Cifras)\n\n"
        "El Banco de Previsión Social (BPS) publica su tablero *BPS en Cifras* "
        "sobre un backend JSON público. Sus datos suelen estar **más "
        "actualizados** que el espejo de datasets del BPS en el Catálogo Nacional "
        "(MIDES / catalogodatos).\n\n"
        "## Principales categorías\n\n"
        "- **Prestaciones**\n"
        "  - *Jubilaciones* — pasividades por jubilación (importes, beneficiarios).\n"
        "  - *Pensiones de sobrevivencia* — pensiones a sobrevivientes.\n"
        "  - *Pensiones asistenciales* — pensiones por vejez/invalidez.\n"
        "  - *Subsidios* — subsidio por desempleo y otros subsidios.\n"
        "- **Recaudación** — ingresos y aportes recaudados.\n"
        "- **Régimen general** — afiliaciones y cobertura del régimen general.\n"
        "- **Cotizantes** — personas y empresas cotizantes.\n\n"
        "## Cómo consultarlas\n\n"
        "1. `bps_listar_categorias` — recorré el árbol de categorías/indicadores "
        "(por defecto sin nodos de prueba).\n"
        "2. `bps_listar_paneles` — obtené los paneles y los ids de bloque que "
        "agrupan.\n"
        "3. `bps_buscar_indicador` — buscá por tema (p.ej. 'jubilaciones') para "
        "localizar el bloque y la pagina de un indicador.\n"
        "4. `bps_indicador` — pasá el bloque para traer la serie (columnas, "
        "n_filas, datos).\n"
        "5. `bps_serie_csv` — pasá el id_pagina para descargar los CSV crudos.\n"
    )


@resource(
    uri="uru://bps/flujo-api",
    name="Flujo de la API del Observatorio del BPS",
    description=(
        "Explica el flujo de descubrimiento del Observatorio del BPS: paneles → "
        "bloques → indicador → datos, y la descarga de series CSV."
    ),
    module=MODULE,
    mime_type="text/markdown",
)
def flujo_api() -> str:
    return (
        "# Flujo de consulta del Observatorio del BPS\n\n"
        "El backend del tablero *BPS en Cifras* organiza los indicadores en "
        "**paneles** que agrupan **bloques**; cada bloque corresponde a un "
        "indicador con su serie de datos.\n\n"
        "## Flujo recomendado\n\n"
        "1. `bps_listar_paneles` — devuelve los paneles, cada uno con su lista de "
        "`bloques`.\n"
        "2. `bps_indicador` — pasá un `bloque` (y opcionalmente `pagina`) para "
        "obtener el indicador: `nombre`, `descripcion`, `columnas`, `n_filas` y "
        "`datos`. Si el bloque no existe, `encontrado` será `False`.\n"
        "3. `bps_serie_csv` — pasá el `id_pagina` (que devuelve `bps_indicador`) "
        "para descargar y descomprimir los archivos CSV crudos de esa página.\n\n"
        "## Búsqueda por tema\n\n"
        "`bps_buscar_indicador` recorre los paneles y sus bloques y devuelve los "
        "indicadores cuyo nombre/descripción coincide con la consulta, con su "
        "`bloque` y `pagina` listos para usar con `bps_indicador`.\n\n"
        "## Categorías\n\n"
        "`bps_listar_categorias` muestra el árbol de categorías/indicadores "
        "(/menu), descartando por defecto los nodos de prueba y conmemorativos.\n"
    )
