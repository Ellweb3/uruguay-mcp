"""MCP prompts for the BCU module (cotizaciones del Banco Central del Uruguay).

Importing this file registers the prompts as a side effect.
"""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE, USD_CODE


@prompt(
    name="bcu_cotizacion_dolar_hoy",
    module=MODULE,
    description="Instrucción para obtener la cotización del dólar hoy según el BCU.",
)
def bcu_cotizacion_dolar_hoy() -> str:
    return (
        "Obtené la cotización más reciente del dólar estadounidense "
        f"(moneda {USD_CODE}) frente al peso uruguayo usando la herramienta "
        "'bcu_cotizacion_usd' (sin indicar fecha, toma el último cierre del BCU). "
        "Indicá compra (TCC), venta (TCV) y la fecha del cierre."
    )


@prompt(
    name="bcu_cotizacion_rango",
    module=MODULE,
    description="Instrucción para consultar la cotización de una moneda en un rango de fechas.",
)
def bcu_cotizacion_rango(
    moneda: int = USD_CODE,
    fecha_desde: str = "",
    fecha_hasta: str = "",
) -> str:
    desde = fecha_desde or "el inicio del período"
    hasta = fecha_hasta or "el último cierre"
    return (
        f"Consultá la cotización de la moneda con código {moneda} entre "
        f"{desde} y {hasta} usando la herramienta 'bcu_cotizaciones' "
        "(parámetros: monedas, fecha_desde, fecha_hasta). Si no conocés el código "
        "de la moneda, usá primero 'bcu_listar_monedas'. Resumí la evolución de "
        "compra (TCC) y venta (TCV) en el período."
    )


@prompt(
    name="bcu_listar_monedas_disponibles",
    module=MODULE,
    description="Instrucción para listar las monedas/divisas cotizadas por el BCU.",
)
def bcu_listar_monedas_disponibles() -> str:
    return (
        "Listá las monedas y divisas cotizadas por el BCU con su código numérico "
        "usando la herramienta 'bcu_listar_monedas' (grupo 2 = divisas). "
        "Mostrá el código y el nombre de cada moneda."
    )
