"""Readable resources for the government news (noticias) module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import BASE_URL, MODULE


@resource(
    uri="uru://noticias/guia-de-uso",
    name="Guía de uso de noticias de gobierno (gub.uy)",
    description="Cómo listar y buscar noticias del Estado uruguayo en gub.uy.",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_de_uso() -> str:
    return (
        "# Guía de uso de noticias de gobierno (gub.uy)\n\n"
        f"Portal oficial del Estado uruguayo ({BASE_URL}). **No existe RSS/Atom/"
        "JSON**: estas herramientas extraen los datos del HTML.\n\n"
        "## Herramientas\n\n"
        "1. **Noticias recientes** de un organismo con `noticias_recientes` "
        "(parámetros: `subsite`, `limit`, `pagina`). Devuelve título, categoría, "
        "fecha (normalizada a ISO), URL y resumen de cada tarjeta del listado, "
        "sin descargar el artículo completo.\n"
        "2. **Búsqueda por texto** con `noticias_buscar` (parámetros: `query`, "
        "`limit`, `subsite`). Usa el buscador de gub.uy y filtra a URLs de "
        "noticias; es `status='partial'`.\n\n"
        "## Subsitios habituales (`subsite`)\n\n"
        "- `presidencia`\n"
        "- `ministerio-salud-publica`\n"
        "- `ministerio-economia-finanzas`\n"
        "- `ministerio-educacion-cultura`\n"
        "- `ministerio-interior`\n\n"
        "## Notas\n\n"
        "- gub.uy es un Drupal con feeds y JSON:API deshabilitados; no hay fuente "
        "legible por máquina, sólo HTML.\n"
        "- Dos diseños de tarjeta conviven entre subsitios (presidencia vs. "
        "ministerios) y dos formatos de fecha ('29 de Mayo, 2026' y "
        "'29/05/2026'); ambos se normalizan a ISO.\n"
        "- `noticias_buscar` devuelve resúmenes del buscador (no el texto del "
        "artículo), sin fecha ni categoría, y puede abarcar varios subsitios.\n"
    )


@resource(
    uri="uru://noticias/subsitios",
    name="Subsitios de noticias de gub.uy",
    description="Listado orientativo de subsitios con listado de noticias.",
    module=MODULE,
    mime_type="text/markdown",
)
def subsitios() -> str:
    return (
        "# Subsitios de noticias de gub.uy\n\n"
        "Slugs de `subsite` para usar con `noticias_recientes`. Cada uno publica "
        f"en `{BASE_URL}/<subsite>/comunicacion/noticias`.\n\n"
        "- `presidencia` — Presidencia de la República\n"
        "- `ministerio-salud-publica` — Ministerio de Salud Pública\n"
        "- `ministerio-economia-finanzas` — Ministerio de Economía y Finanzas\n"
        "- `ministerio-educacion-cultura` — Ministerio de Educación y Cultura\n"
        "- `ministerio-interior` — Ministerio del Interior\n"
        "- `ministerio-trabajo-seguridad-social` — Ministerio de Trabajo y "
        "Seguridad Social\n"
        "- `ministerio-ganaderia-agricultura-pesca` — MGAP\n"
        "- `ministerio-relaciones-exteriores` — Cancillería\n"
    )
