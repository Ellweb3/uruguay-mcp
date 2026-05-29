"""Reusable MCP prompts for the Intendencia de Montevideo module.

Each prompt returns a ready-to-use instruction in Spanish that orients the
model toward the module's real tools (próximo bus, buses cercanos, multas).
"""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="montevideo_proximo_bus",
    module=MODULE,
    description=(
        "Genera una instrucción para averiguar el próximo bus en una parada de "
        "Montevideo a partir de una calle o un id de parada."
    ),
)
def montevideo_proximo_bus(parada: str, lineas: str = "") -> str:
    lineas_txt = (
        f"Las líneas de interés son: {lineas}. "
        if lineas
        else (
            "Si no se conocen las líneas, primero obtené las que pasan por la "
            "parada con montevideo_busstop_lines. "
        )
    )
    return (
        f"Averiguá el próximo bus en la parada '{parada}' de Montevideo. "
        "Si te dieron una calle o esquina y no un id numérico, resolvé el "
        "busstop_id con montevideo_list_busstops. "
        f"{lineas_txt}"
        "Luego consultá los tiempos de arribo con montevideo_bus_eta pasando "
        "busstop_id y lines. Aclarale al usuario que la unidad de 'eta' no está "
        "documentada (puede venir en segundos o minutos) y que el transporte "
        "requiere credenciales OAuth2."
    )


@prompt(
    name="montevideo_buses_cercanos",
    module=MODULE,
    description=(
        "Genera una instrucción para listar los buses de Montevideo cerca de un "
        "punto geográfico dado."
    ),
)
def montevideo_buses_cercanos(lat: float, lng: float, radio_m: float = 500) -> str:
    return (
        f"Listá los buses de Montevideo en tiempo real dentro de {radio_m} metros "
        f"del punto ({lat}, {lng}). Usá montevideo_buses_near con lat, lng y "
        "radius_m. Resumí por línea (line), empresa (companyName) y destino "
        "(destination), e indicá cuántos vehículos hay en el radio. Recordá que "
        "el transporte requiere credenciales OAuth2."
    )


@prompt(
    name="montevideo_multas_resumen",
    module=MODULE,
    description=(
        "Genera una instrucción para resumir los datos abiertos AGREGADOS de "
        "multas de tránsito (SUCIVE) de la Intendencia de Montevideo."
    ),
)
def montevideo_multas_resumen(anio: int | None = None) -> str:
    filtro = (
        f"Enfocate en los archivos del año {anio}. "
        if anio is not None
        else "Mostrá los archivos anuales disponibles y las tablas de referencia. "
    )
    return (
        "Resumí los datos abiertos de multas de tránsito (SUCIVE) de la "
        "Intendencia de Montevideo usando montevideo_multas_transito"
        + (f" con year={anio}." if anio is not None else ".")
        + " "
        + filtro
        + "Dejá claro que son datos ESTADÍSTICOS/AGREGADOS (no una consulta de "
        "deuda por matrícula) y que los recursos sin datastore se descargan "
        "desde su 'url'."
    )
