"""Readable MCP resources for the DGI (Dirección General Impositiva) module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import MODULE


@resource(
    uri="uru://dgi/catalogo-valores",
    name="Catálogo de valores de referencia de la DGI",
    description=(
        "Panorama de las tablas de valores fiscales que publica la DGI (Unidad "
        "Indexada, IPC, coeficientes ITP/activo fijo, tasas de recargos) y cómo "
        "consultarlas."
    ),
    module=MODULE,
    mime_type="text/markdown",
)
def catalogo_valores() -> str:
    return (
        "# Valores de referencia de la DGI\n\n"
        "La Dirección General Impositiva (DGI) publica en gub.uy planillas "
        "descargables (`.ods`/`.xlsx`/`.csv`) con los **valores fiscales de "
        "referencia** que alimentan los cálculos de impuestos y de recargos por "
        "mora. No hay API: estos archivos se extraen de los enlaces del HTML.\n\n"
        "## Tablas principales\n\n"
        "- **Unidad Indexada (UI)** — valor diario de la UI por año.\n"
        "- **Índice de Precios al Consumo (IPC)** — serie del IPC.\n"
        "- **Cotizaciones interbancarias** (compra billetes) por año.\n"
        "- **Coeficiente de ajuste de inmuebles (ITP)** — para el Impuesto a las "
        "Transmisiones Patrimoniales.\n"
        "- **Coeficientes de revaluación del activo fijo**.\n"
        "- **Tasas de interés mensual de recargos (Art. 94)** — recargos por "
        "mora.\n"
        "- **Tasas de interés mensual por facilidades (Art. 33° C.T.)**.\n\n"
        "Estos valores alimentan el cálculo de impuestos y, sobre todo, de "
        "**recargos por mora** y convenios de facilidades de pago.\n\n"
        "## Cómo consultarlas\n\n"
        "1. `dgi_buscar_valor` — buscá por tema (p.ej. 'unidad indexada', "
        "'recargos por mora') y obtené una vista previa de la tabla más "
        "reciente.\n"
        "2. `dgi_listar_datos` — listá todos los archivos disponibles (filtrá "
        "por tema y/o formato) con su período de publicación.\n"
        "3. `dgi_tabla` — pasá la `url` de un archivo para leer sus filas (los "
        "`.ods` traen varias hojas; elegí `hoja`).\n"
    )


@resource(
    uri="uru://dgi/fuentes",
    name="Fuentes y alcance de los datos de la DGI",
    description=(
        "Explica que los datos de la DGI son .ods/.pdf scrapeados de gub.uy y "
        "que no hay API por contribuyente ni cálculo en vivo."
    ),
    module=MODULE,
    mime_type="text/markdown",
)
def fuentes() -> str:
    return (
        "# Fuentes y alcance del módulo DGI\n\n"
        "La DGI **no expone una API**. Sus datos abiertos son archivos "
        "descargables publicados como enlaces directos dentro de páginas HTML "
        "del sitio Drupal de la DGI en gub.uy:\n\n"
        "- **Planillas `.ods`/`.xlsx`/`.csv`** con valores fiscales de "
        "referencia (Unidad Indexada, IPC, coeficientes ITP/activo fijo, tasas "
        "de recargos Art.94 y de facilidades Art.33).\n"
        "- **Boletines estadísticos `.pdf`** (anuales) y los PDFs de gasto "
        "tributario.\n\n"
        "Este módulo descarga ese HTML, extrae los enlaces y parsea las "
        "planillas con la biblioteca estándar (sin dependencias extra).\n\n"
        "## Fuera de alcance\n\n"
        "- **No hay consulta por contribuyente ni cálculo en vivo**: RUT, "
        "IVA/IRPF, y declaraciones están detrás de ID Uruguay / certificado y no "
        "son datos abiertos.\n"
        "- **El tipo de cambio diario NO está acá**: eso es el módulo `bcu`.\n\n"
        "## Herramientas\n\n"
        "- `dgi_listar_datos` — listar los archivos de valores de referencia.\n"
        "- `dgi_buscar_valor` — buscar y previsualizar un valor por tema.\n"
        "- `dgi_tabla` — leer una planilla (`.ods`/`.xlsx`/`.csv`) por su url.\n"
        "- `dgi_boletines` — listar los boletines estadísticos (PDF).\n"
    )
