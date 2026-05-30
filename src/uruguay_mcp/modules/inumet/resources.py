"""Recursos de referencia para el módulo de INUMET (clima de Uruguay)."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import BASE_URL, MODULE


@resource(
    uri="uru://inumet/guia-de-uso",
    name="Guía de uso de los datos meteorológicos de INUMET",
    description="Cómo consultar estaciones, pronóstico y alertas de INUMET.",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_de_uso() -> str:
    return (
        "# Guía de uso de los datos de INUMET\n\n"
        f"Instituto Uruguayo de Meteorología ({BASE_URL}). Acceso público, sin "
        "autenticación. Contenido en español.\n\n"
        "## Herramientas\n\n"
        "1. **Estaciones automáticas (EMA)** con `inumet_estaciones`: "
        "observaciones actuales (temperatura, humedad, viento, presión, "
        "precipitación, visibilidad) de las estaciones de todo el país. Filtros: "
        "`station` (nombre/ID) y `automatic_only`.\n"
        "2. **Pronóstico** con `inumet_pronostico`: pronóstico oficial de ~4 días "
        "(mínima, máxima y descripción por período). Parámetro `days`.\n"
        "3. **Alertas** con `inumet_alertas`: advertencias meteorológicas vigentes "
        "(activa sí/no, nivel amarilla/naranja/roja, texto y PDF si existe).\n\n"
        "## Notas técnicas\n\n"
        "- Las velocidades de viento del EMA vienen en **nudos** (`viento_kt`); el "
        "campo `viento_kmh` ofrece la conversión (x1,852).\n"
        "- Las marcas de tiempo (`timestamp`) están en hora local de Uruguay "
        "(offset -03:00).\n"
        "- El pronóstico y las alertas se obtienen scrapeando páginas HTML de "
        "Drupal (no hay API JSON). Si la estructura cambia, la respuesta degrada a "
        "`status: 'partial'` en lugar de inventar datos.\n"
        "- Los datos del EMA se cachean ~5 minutos (max-age=300 del servidor).\n"
    )


@resource(
    uri="uru://inumet/variables",
    name="Variables meteorológicas de las estaciones EMA",
    description="Significado y unidades de los campos devueltos por inumet_estaciones.",
    module=MODULE,
    mime_type="text/markdown",
)
def variables() -> str:
    return (
        "# Variables de las estaciones automáticas (EMA)\n\n"
        "Campos slim que devuelve `inumet_estaciones` por estación:\n\n"
        "- `temp_c`: temperatura del aire (°C)\n"
        "- `hum_pct`: humedad relativa (%)\n"
        "- `viento_kt` / `viento_kmh`: intensidad del viento (nudos / km/h)\n"
        "- `dir_viento_grados`: dirección del viento (grados)\n"
        "- `rafaga_kt` / `rafaga_kmh`: intensidad de ráfaga (nudos / km/h)\n"
        "- `presion_hpa`: presión atmosférica a nivel del mar (hPa)\n"
        "- `precip_mm`: precipitación horaria (mm)\n"
        "- `visibilidad_km`: visibilidad (km)\n"
        "- `timestamp`: hora local (-03:00) de la observación más reciente\n\n"
        "Además: `id`, `idStr`, `nombre`, `lat`, `lon`, `altitud`, `gerencia`.\n\n"
        "Nota: el conjunto incluye estaciones fronterizas no uruguayas (INMET de "
        "Brasil, SMN Aeroparque de Argentina, Antártida). Usá `gerencia` o "
        "`lat`/`lon` para filtrar a Uruguay si lo necesitás.\n"
    )
