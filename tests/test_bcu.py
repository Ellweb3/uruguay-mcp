"""Unit tests for the BCU SOAP module, with the zeep client mocked.

The BCU services are SOAP (no REST), so there is no httpx traffic to intercept
with respx for the happy path; instead we replace ``client._get_client`` with a
fake zeep client whose ``service.Execute`` returns the documented shapes. A
``respx`` import is kept (per template) and used to assert no stray HTTP leaks.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import httpx  # noqa: F401 — template parity / available for live mocks
import pytest
import respx  # noqa: F401

import uruguay_mcp.modules.bcu  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.bcu import client
from uruguay_mcp.modules.bcu.constants import USD_CODE
from uruguay_mcp.shared import cache, http


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    client._clients.clear()
    yield
    cache.clear()
    client._clients.clear()
    await http.aclose()


class _FakeFactory:
    """Mimics zeep's type_factory: each type is a callable returning its kwargs."""

    def __getitem__(self, name: str):
        def _make(**kwargs: Any) -> dict[str, Any]:
            return {"__type__": name, **kwargs}

        return _make


def _fake_client(execute):
    """Build a fake zeep-like client whose service.Execute delegates to ``execute``."""
    service = SimpleNamespace(Execute=execute)
    return SimpleNamespace(
        service=service,
        type_factory=lambda ns: _FakeFactory(),
    )


def _install(monkeypatch, by_wsdl):
    async def fake_get_client(wsdl: str):
        return by_wsdl[wsdl]

    monkeypatch.setattr(client, "_get_client", fake_get_client)
    # serialize_object passthrough: our fakes already return plain dicts/lists.
    monkeypatch.setattr(client, "_serialize", lambda obj: obj)


async def test_ultimo_cierre(monkeypatch):
    from uruguay_mcp.modules.bcu.constants import WSDL_ULTIMO_CIERRE

    def execute():
        return {"Fecha": date(2026, 5, 29)}

    _install(monkeypatch, {WSDL_ULTIMO_CIERRE: _fake_client(execute)})

    out = await meta.call_tool("bcu_ultimo_cierre", {})
    assert out["_meta"]["source"]["api"] == "bcu.gub.uy / cotizaciones"
    assert out["_meta"]["cached"] is False
    assert out["data"]["fecha"] == "2026-05-29"


async def test_listar_monedas_slims(monkeypatch):
    from uruguay_mcp.modules.bcu.constants import WSDL_MONEDAS

    def execute(inp):
        assert inp["Grupo"] == 2
        # zeep collapses the wrapper: a list is returned directly.
        return [
            {"Codigo": 2225, "Nombre": "DLS. USA BILLETE"},
            {"Codigo": 1001, "Nombre": "REAL BILLETE"},
        ]

    _install(monkeypatch, {WSDL_MONEDAS: _fake_client(execute)})

    out = await meta.call_tool("bcu_listar_monedas", {"grupo": 2})
    data = out["data"]
    assert {"codigo": 2225, "nombre": "DLS. USA BILLETE"} in data
    assert len(data) == 2


def _cotiz_ok(monedas):
    rows = [
        {
            "Fecha": date(2026, 5, 29),
            "Moneda": 2225,
            "Nombre": "DLS. USA BILLETE",
            "CodigoISO": "DLS.",
            "Emisor": "USA",
            "TCC": 40.0,
            "TCV": 40.064,
            "ArbAct": 1.0,
            "FormaArbitrar": 0,
        }
    ]
    return {
        "respuestastatus": {"status": 1, "codigoerror": 0, "mensaje": ""},
        "datoscotizaciones": {"datoscotizaciones.dato": rows},
    }


async def test_cotizacion_usd_uses_ultimo_cierre(monkeypatch):
    from uruguay_mcp.modules.bcu.constants import WSDL_COTIZACIONES, WSDL_ULTIMO_CIERRE

    def cierre_exec():
        return {"Fecha": date(2026, 5, 29)}

    def cotiz_exec(inp):
        assert inp["Moneda"]["item"] == [USD_CODE]
        assert inp["FechaDesde"] == date(2026, 5, 29)
        assert inp["FechaHasta"] == date(2026, 5, 29)
        return _cotiz_ok([USD_CODE])

    _install(
        monkeypatch,
        {
            WSDL_ULTIMO_CIERRE: _fake_client(cierre_exec),
            WSDL_COTIZACIONES: _fake_client(cotiz_exec),
        },
    )

    out = await meta.call_tool("bcu_cotizacion_usd", {})
    data = out["data"]
    assert data["fecha"] == "2026-05-29"
    cot = data["cotizaciones"][0]
    assert cot["moneda"] == 2225
    assert cot["compra"] == 40.0
    assert cot["venta"] == 40.064
    assert cot["fecha"] == "2026-05-29"


async def test_cotizaciones_explicit_range(monkeypatch):
    from uruguay_mcp.modules.bcu.constants import WSDL_COTIZACIONES

    def cotiz_exec(inp):
        assert inp["FechaDesde"] == date(2026, 5, 20)
        return _cotiz_ok([USD_CODE])

    _install(monkeypatch, {WSDL_COTIZACIONES: _fake_client(cotiz_exec)})

    out = await meta.call_tool(
        "bcu_cotizaciones",
        {"monedas": [2225], "fecha_desde": "2026-05-20", "fecha_hasta": "2026-05-29"},
    )
    data = out["data"]
    assert data["fecha_desde"] == "2026-05-20"
    assert data["fecha_hasta"] == "2026-05-29"
    assert len(data["cotizaciones"]) == 1


async def test_no_data_status_becomes_error_envelope(monkeypatch):
    from uruguay_mcp.modules.bcu.constants import WSDL_COTIZACIONES

    def cotiz_exec(inp):
        # weekend/holiday: SOAP succeeds but status != 1 with a junk row.
        return {
            "respuestastatus": {
                "status": 0,
                "codigoerror": 100,
                "mensaje": "No existe cotizacion para la fecha indicada",
            },
            "datoscotizaciones": {
                "datoscotizaciones.dato": [
                    {"Fecha": None, "Moneda": 0, "TCC": 0.0, "TCV": 0.0}
                ]
            },
        }

    _install(monkeypatch, {WSDL_COTIZACIONES: _fake_client(cotiz_exec)})

    out = await meta.call_tool(
        "bcu_cotizaciones",
        {"monedas": [2225], "fecha_desde": "2026-05-24", "fecha_hasta": "2026-05-24"},
    )
    assert out["error"]["code"] == "upstream_error"


def test_bcu_prompts_registered():
    from uruguay_mcp.shared.registry import registry

    names = {p.name for p in registry.prompts() if p.module == "bcu"}
    assert {
        "bcu_cotizacion_dolar_hoy",
        "bcu_cotizacion_rango",
        "bcu_listar_monedas_disponibles",
    } <= names


def test_bcu_resources_registered():
    from uruguay_mcp.shared.registry import registry

    uris = {r.uri for r in registry.resources() if r.module == "bcu"}
    assert "uru://bcu/codigos-moneda" in uris
    assert "uru://bcu/grupos-moneda" in uris


async def test_listar_monedas_is_cached(monkeypatch):
    from uruguay_mcp.modules.bcu.constants import WSDL_MONEDAS

    calls = {"n": 0}

    def execute(inp):
        calls["n"] += 1
        return [{"Codigo": 2225, "Nombre": "DLS. USA BILLETE"}]

    _install(monkeypatch, {WSDL_MONEDAS: _fake_client(execute)})

    first = await meta.call_tool("bcu_listar_monedas", {"grupo": 2})
    second = await meta.call_tool("bcu_listar_monedas", {"grupo": 2})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert calls["n"] == 1
