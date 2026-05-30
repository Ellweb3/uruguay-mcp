"""Prompts reutilizables para el módulo de INUMET (clima de Uruguay)."""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="inumet_clima_actual",
    module=MODULE,
    description="Instrucción para reportar el clima actual de una localidad usando estaciones EMA.",
)
def inumet_clima_actual(localidad: str = "Montevideo") -> str:
    return (
        f"Reportá el clima actual de '{localidad}' en Uruguay usando la herramienta "
        "inumet_estaciones (parámetro station con el nombre de la localidad o la "
        "estación más cercana). Indicá temperatura (temp_c), humedad (hum_pct), "
        "viento (viento_kmh y dir_viento_grados) y, si aplica, precipitación "
        "(precip_mm), junto con la hora de la observación (timestamp). Si no hay "
        "una estación con ese nombre, mostrá las estaciones disponibles más cercanas."
    )


@prompt(
    name="inumet_resumen_tiempo",
    module=MODULE,
    description="Instrucción para resumir el pronóstico y las alertas vigentes de Uruguay.",
)
def inumet_resumen_tiempo(dias: int = 4) -> str:
    return (
        f"Armá un resumen del tiempo en Uruguay para los próximos {dias} días. "
        "Primero consultá inumet_pronostico (parámetro days) para las mínimas, "
        "máximas y descripción por período de cada día. Luego verificá si hay "
        "advertencias vigentes con inumet_alertas e indicá su nivel "
        "(amarilla/naranja/roja) y zonas afectadas si está activa. Cerrá con una "
        "recomendación breve para la población."
    )
