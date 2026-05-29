"""Async wrapper over the BCU SOAP services.

``zeep`` is synchronous and blocking — both building a ``Client`` (it downloads
and parses the WSDL) and invoking ``service.Execute(...)`` block the event loop.
Every such call is therefore pushed to a worker thread via ``asyncio.to_thread``.
Clients are built lazily and cached per WSDL.

Response shapes follow the documented BCU gotchas:
- ``monedas``: ``Execute()`` returns the list of ``{Codigo, Nombre}`` directly.
- ``cotizaciones``: data lives at ``resp['datoscotizaciones']['datoscotizaciones.dato']``;
  a no-data result still "succeeds" at SOAP level with ``respuestastatus.status != 1``
  and a single junk row (``Fecha`` None / ``Moneda`` 0), which we filter out.
"""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

from ...shared import cache, errors
from .constants import (
    API_NAME,
    WSDL_COTIZACIONES,
    WSDL_MONEDAS,
    WSDL_ULTIMO_CIERRE,
)

_clients: dict[str, Any] = {}


def _build_client(wsdl: str) -> Any:
    """Build (and parse the WSDL for) a zeep client. Blocking — call in a thread."""
    from zeep import Client  # imported lazily so the module loads without network

    return Client(wsdl)


async def _get_client(wsdl: str) -> Any:
    client = _clients.get(wsdl)
    if client is None:
        try:
            client = await asyncio.to_thread(_build_client, wsdl)
        except Exception as exc:  # noqa: BLE001 — surface any WSDL/transport failure
            raise errors.upstream(API_NAME, f"no se pudo cargar el WSDL: {exc}") from exc
        _clients[wsdl] = client
    return client


def _serialize(obj: Any) -> Any:
    from zeep.helpers import serialize_object

    return serialize_object(obj)


async def ultimo_cierre() -> tuple[date, bool, str]:
    """Return the date of the latest published closing (cached)."""

    async def producer() -> date:
        client = await _get_client(WSDL_ULTIMO_CIERRE)
        try:
            resp = await asyncio.to_thread(client.service.Execute)
        except Exception as exc:  # noqa: BLE001
            raise errors.upstream(API_NAME, str(exc)) from exc
        data = _serialize(resp)
        fecha = data.get("Fecha") if isinstance(data, dict) else getattr(resp, "Fecha", None)
        if not isinstance(fecha, date):
            raise errors.upstream(API_NAME, "respuesta de último cierre inválida")
        return fecha

    value, cached = await cache.get_or_set("bcu:ultimo_cierre", producer)
    return value, cached, WSDL_ULTIMO_CIERRE


async def listar_monedas(grupo: int) -> tuple[list[dict[str, Any]], bool, str]:
    """Return the list of currencies for a group (cached)."""

    async def producer() -> list[dict[str, Any]]:
        client = await _get_client(WSDL_MONEDAS)
        factory = client.type_factory("ns0")
        inp = factory["wsmonedasin"](Grupo=grupo)
        try:
            resp = await asyncio.to_thread(client.service.Execute, inp)
        except Exception as exc:  # noqa: BLE001
            raise errors.upstream(API_NAME, str(exc)) from exc
        # zeep collapses the wrapper: Execute() returns the list directly.
        rows = _serialize(resp) or []
        if isinstance(rows, dict):  # defensive: some zeep versions keep the wrapper
            rows = rows.get("wsmonedasout.Linea") or []
        return [dict(r) for r in rows]

    value, cached = await cache.get_or_set(f"bcu:monedas:{grupo}", producer)
    return value, cached, WSDL_MONEDAS


async def cotizaciones(
    monedas: list[int], fecha_desde: date, fecha_hasta: date, grupo: int
) -> tuple[list[dict[str, Any]], bool, str]:
    """Return exchange-rate rows for the given currencies/date range (cached)."""

    async def producer() -> list[dict[str, Any]]:
        client = await _get_client(WSDL_COTIZACIONES)
        factory = client.type_factory("ns0")
        arr = factory["ArrayOfint"](item=list(monedas))
        inp = factory["wsbcucotizacionesin"](
            Moneda=arr,
            FechaDesde=fecha_desde,
            FechaHasta=fecha_hasta,
            Grupo=grupo,
        )
        try:
            resp = await asyncio.to_thread(client.service.Execute, inp)
        except Exception as exc:  # noqa: BLE001
            raise errors.upstream(API_NAME, str(exc)) from exc

        data = _serialize(resp) or {}
        status = (data.get("respuestastatus") or {}) if isinstance(data, dict) else {}
        if status.get("status") != 1:
            mensaje = status.get("mensaje") or "sin cotización para el rango indicado"
            raise errors.upstream(API_NAME, str(mensaje))

        container = data.get("datoscotizaciones") or {}
        rows = container.get("datoscotizaciones.dato") or []
        # Filter junk rows (no-data sentinel: Fecha None, Moneda 0).
        return [
            dict(r)
            for r in rows
            if r and r.get("Fecha") is not None and r.get("Moneda")
        ]

    codes = ",".join(str(c) for c in sorted(monedas))
    key = f"bcu:cotiz:{grupo}:{codes}:{fecha_desde.isoformat()}:{fecha_hasta.isoformat()}"
    value, cached = await cache.get_or_set(key, producer)
    return value, cached, WSDL_COTIZACIONES
