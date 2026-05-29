"""Discoverable tools for BCU exchange rates (cotizaciones del BCU)."""

from __future__ import annotations

from datetime import date
from typing import Any

from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import API_NAME, GROUP_DIVISAS, MODULE, USD_CODE
from .schemas import (
    CotizacionesArgs,
    CotizacionUsdArgs,
    ListarMonedasArgs,
    UltimoCierreArgs,
)


def _slim_moneda(row: dict[str, Any]) -> dict[str, Any]:
    return {"codigo": row.get("Codigo"), "nombre": row.get("Nombre")}


def _slim_cotizacion(row: dict[str, Any]) -> dict[str, Any]:
    fecha = row.get("Fecha")
    return {
        "fecha": fecha.isoformat() if isinstance(fecha, date) else fecha,
        "moneda": row.get("Moneda"),
        "nombre": row.get("Nombre"),
        "codigo_iso": row.get("CodigoISO"),
        "emisor": row.get("Emisor"),
        "compra": row.get("TCC"),
        "venta": row.get("TCV"),
        "arbitraje": row.get("ArbAct"),
    }


@tool(
    name="bcu_listar_monedas",
    module=MODULE,
    summary=(
        "Listar las monedas/divisas cotizadas por el BCU con su código numérico "
        "(ej. 2225 = DLS. USA BILLETE). Necesario para conocer el código antes de "
        "pedir cotizaciones."
    ),
    params_model=ListarMonedasArgs,
    keywords=[
        "bcu", "moneda", "monedas", "divisa", "currency", "codigo", "dolar",
        "usd", "uruguay", "tipo de cambio",
    ],
)
async def listar_monedas(grupo: int = GROUP_DIVISAS) -> dict[str, Any]:
    rows, cached, url = await client.listar_monedas(grupo)
    data = [_slim_moneda(r) for r in rows]
    return envelope(data, api=API_NAME, url=url, cached=cached)


@tool(
    name="bcu_ultimo_cierre",
    module=MODULE,
    summary=(
        "Obtener la fecha del último cierre (último día hábil con cotizaciones "
        "publicadas por el BCU). Útil como fecha por defecto para el tipo de cambio "
        "más reciente."
    ),
    params_model=UltimoCierreArgs,
    keywords=[
        "bcu", "ultimo cierre", "fecha", "ultima cotizacion", "hoy", "reciente",
        "uruguay",
    ],
)
async def ultimo_cierre() -> dict[str, Any]:
    fecha, cached, url = await client.ultimo_cierre()
    return envelope({"fecha": fecha.isoformat()}, api=API_NAME, url=url, cached=cached)


@tool(
    name="bcu_cotizaciones",
    module=MODULE,
    summary=(
        "Obtener cotizaciones (tipo de cambio compra TCC y venta TCV) de una o "
        "varias monedas del BCU para un rango de fechas. Ej. dólar (2225) entre dos "
        "fechas."
    ),
    params_model=CotizacionesArgs,
    keywords=[
        "bcu", "cotizacion", "cotizaciones", "tipo de cambio", "dolar", "usd",
        "tcc", "tcv", "compra", "venta", "rango", "historico", "uruguay",
        "exchange rate",
    ],
)
async def cotizaciones(
    monedas: list[int] | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    grupo: int = GROUP_DIVISAS,
) -> dict[str, Any]:
    monedas = monedas if monedas is not None else [USD_CODE]
    cached_cierre = True  # "not fetched" counts as cached for the aggregate flag
    if fecha_desde is None or fecha_hasta is None:
        cierre, cached_cierre, _ = await client.ultimo_cierre()
        fecha_desde = fecha_desde or cierre
        fecha_hasta = fecha_hasta or cierre

    rows, cached, url = await client.cotizaciones(monedas, fecha_desde, fecha_hasta, grupo)
    data = {
        "fecha_desde": fecha_desde.isoformat(),
        "fecha_hasta": fecha_hasta.isoformat(),
        "cotizaciones": [_slim_cotizacion(r) for r in rows],
    }
    return envelope(data, api=API_NAME, url=url, cached=cached and cached_cierre)


@tool(
    name="bcu_cotizacion_usd",
    module=MODULE,
    summary=(
        "Atajo: obtener la cotización del dólar estadounidense (moneda 2225) para "
        "una fecha (o el último cierre si no se indica). Devuelve compra y venta."
    ),
    params_model=CotizacionUsdArgs,
    keywords=[
        "bcu", "dolar", "usd", "tipo de cambio dolar", "cotizacion dolar",
        "cuanto vale el dolar", "uruguay", "cambio",
    ],
)
async def cotizacion_usd(fecha: date | None = None) -> dict[str, Any]:
    cached_cierre = True  # "not fetched" counts as cached for the aggregate flag
    if fecha is None:
        fecha, cached_cierre, _ = await client.ultimo_cierre()

    rows, cached, url = await client.cotizaciones([USD_CODE], fecha, fecha, GROUP_DIVISAS)
    data = {
        "fecha": fecha.isoformat(),
        "cotizaciones": [_slim_cotizacion(r) for r in rows],
    }
    return envelope(data, api=API_NAME, url=url, cached=cached and cached_cierre)
