"""Unit tests for the INUMET module, with the HTTP layer mocked.

Covers the three surfaces: the EMA JSON endpoint and the two HTML-scraped pages
(pronóstico and alertas). All tests run offline (no live network).
"""

from __future__ import annotations

import httpx
import pytest
import respx

import uruguay_mcp.modules.inumet  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.inumet.constants import ALERTA_URL, EMA_URL, PRONOSTICO_URL
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


# A tiny EMA payload: 2 stations (1 automatic, 1 not), 3 timestamps, and two
# variables (TempAire id=47 at variables[0], IntViento id=29 at variables[1]).
def _ema_payload() -> dict:
    return {
        "estaciones": [
            {
                "id": 1,
                "idStr": "AERO",
                "displayNamePublic": "Aeropuerto de Carmelo",
                "nombre": "Carmelo",
                "latitud": -34.0,
                "longitud": -58.3,
                "altitud": 20,
                "gerencia": "Litoral",
                "tipoAutomatica": True,
            },
            {
                "id": 2,
                "idStr": "MAN",
                "displayNamePublic": "Estación Manual",
                "nombre": "Manual",
                "latitud": -33.0,
                "longitud": -56.0,
                "altitud": 50,
                "gerencia": "Centro",
                "tipoAutomatica": False,
            },
        ],
        "variables": [
            {"id": 47, "idStr": "TempAire", "nombre": "TempAire", "unidad": "C"},
            {"id": 29, "idStr": "IntViento", "nombre": "IntViento", "unidad": "nudos"},
        ],
        "fechas": [
            "2026-05-29T20:00:00.000-03:00",
            "2026-05-29T21:00:00.000-03:00",
            "2026-05-29T22:00:00.000-03:00",
        ],
        "observaciones": [
            {  # TempAire — last non-null for station 0 is at index 2 (11.8)
                "iFechas": [0, 1, 2],
                "datos": [[10.0, None, 11.8], [9.0, 9.5, None]],
            },
            {  # IntViento — station 0 latest non-null at index 2 (10 kt)
                "iFechas": [0, 1, 2],
                "datos": [[None, 8.0, 10.0], [5.0, None, None]],
            },
        ],
    }


@respx.mock
async def test_estaciones_parses_matrix_and_slims():
    route = respx.get(EMA_URL).mock(return_value=httpx.Response(200, json=_ema_payload()))

    out = await meta.call_tool("inumet_estaciones", {})

    assert route.called
    assert out["_meta"]["source"]["api"] == "inumet.gub.uy"
    assert out["_meta"]["cached"] is False
    body = out["data"]
    # Only the automatic station is returned by default.
    assert body["count"] == 1
    est = body["estaciones"][0]
    assert est["nombre"] == "Aeropuerto de Carmelo"
    assert est["temp_c"] == 11.8
    assert est["viento_kt"] == 10.0
    assert est["viento_kmh"] == round(10.0 * 1.852, 1)
    # Latest reading timestamp picks the most recent non-null fecha.
    assert est["timestamp"] == "2026-05-29T22:00:00.000-03:00"


@respx.mock
async def test_estaciones_include_manual_and_filter():
    respx.get(EMA_URL).mock(return_value=httpx.Response(200, json=_ema_payload()))

    out = await meta.call_tool(
        "inumet_estaciones", {"automatic_only": False, "station": "Manual"}
    )
    body = out["data"]
    assert body["count"] == 1
    assert body["estaciones"][0]["idStr"] == "MAN"


@respx.mock
async def test_estaciones_is_cached_second_call():
    route = respx.get(EMA_URL).mock(return_value=httpx.Response(200, json=_ema_payload()))

    first = await meta.call_tool("inumet_estaciones", {})
    second = await meta.call_tool("inumet_estaciones", {})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


@respx.mock
async def test_estaciones_upstream_error_envelope():
    respx.get(EMA_URL).mock(return_value=httpx.Response(500))

    out = await meta.call_tool("inumet_estaciones", {})
    assert out["error"]["code"] == "upstream_error"


_PRONOSTICO_HTML = """
<html><body><main>
<div class="pronostico-item">
  <h3>Viernes 29</h3>
  <span>Temp. mín. 8 ºC máx. 15 ºC</span>
  <div class="pronostico-desc">Mañana: Nuboso, cubierto. Viento: Sector E 10-30 km/h</div>
  <div class="pronostico-desc">Tarde/Noche: Lluvias escasas. Viento: Sector S 20-40 km/h</div>
</div>
<div class="pronostico-item">
  <h3>Sábado 30</h3>
  <span>Temp. mín. 6 ºC máx. 12 ºC</span>
  <div class="pronostico-desc">Mañana: Despejado. Viento: Sector SO 5-15 km/h</div>
</div>
</main></body></html>
"""


@respx.mock
async def test_pronostico_parses_days():
    route = respx.get(PRONOSTICO_URL).mock(
        return_value=httpx.Response(200, text=_PRONOSTICO_HTML)
    )

    out = await meta.call_tool("inumet_pronostico", {"days": 4})

    assert route.called
    body = out["data"]
    assert body["status"] == "ok"
    assert body["count"] == 2
    d0 = body["dias"][0]
    assert d0["dia"].lower().startswith("viernes")
    assert d0["temp_min_c"] == 8
    assert d0["temp_max_c"] == 15
    assert len(d0["periodos"]) == 2
    assert "Nuboso" in d0["periodos"][0]["descripcion"]
    assert "Sector E" in d0["periodos"][0]["viento"]


@respx.mock
async def test_pronostico_degrades_when_unparseable():
    respx.get(PRONOSTICO_URL).mock(
        return_value=httpx.Response(200, text="<html><body>sin pronóstico</body></html>")
    )

    out = await meta.call_tool("inumet_pronostico", {})
    body = out["data"]
    assert body["status"] == "partial"
    assert out["_meta"]["status"] == "partial"
    assert body["count"] == 0


@respx.mock
async def test_pronostico_respects_days_limit():
    respx.get(PRONOSTICO_URL).mock(
        return_value=httpx.Response(200, text=_PRONOSTICO_HTML)
    )

    out = await meta.call_tool("inumet_pronostico", {"days": 1})
    assert out["data"]["count"] == 1


@respx.mock
async def test_alertas_no_active_warning():
    html = (
        "<html><body><main>No hay advertencia meteorológica vigente. "
        "Descargar Advertencia Meteorológica.</main></body></html>"
    )
    route = respx.get(ALERTA_URL).mock(return_value=httpx.Response(200, text=html))

    out = await meta.call_tool("inumet_alertas", {})

    assert route.called
    body = out["data"]
    assert body["activa"] is False
    assert body["status"] == "ok"
    assert body["nivel"] is None


@respx.mock
async def test_alertas_active_warning_detects_level_and_pdf():
    html = (
        '<html><body><main>Advertencia meteorológica nivel naranja por '
        'tormentas fuertes en el sur del país. '
        '<a href="/files/adv-2026.pdf">Descargar</a></main></body></html>'
    )
    respx.get(ALERTA_URL).mock(return_value=httpx.Response(200, text=html))

    out = await meta.call_tool("inumet_alertas", {})
    body = out["data"]
    assert body["activa"] is True
    assert body["nivel"] == "naranja"
    assert body["pdf_url"] == "https://www.inumet.gub.uy/files/adv-2026.pdf"
    assert "tormentas" in body["detalle"]


@respx.mock
async def test_alertas_upstream_error_envelope():
    respx.get(ALERTA_URL).mock(return_value=httpx.Response(503))

    out = await meta.call_tool("inumet_alertas", {})
    assert out["error"]["code"] == "upstream_error"


def test_module_prompts_registered_and_reference_real_tools():
    by_name = {p.name: p for p in registry.prompts() if p.module == "inumet"}
    assert {"inumet_clima_actual", "inumet_resumen_tiempo"} <= set(by_name)
    text = by_name["inumet_clima_actual"].handler(localidad="Salto")
    assert "inumet_estaciones" in text
    resumen = by_name["inumet_resumen_tiempo"].handler()
    assert "inumet_pronostico" in resumen
    assert "inumet_alertas" in resumen


def test_module_resources_registered():
    uris = {r.uri for r in registry.resources() if r.module == "inumet"}
    assert {
        "uru://inumet/guia-de-uso",
        "uru://inumet/variables",
    } <= uris


def test_inumet_new_prompt_registered():
    names = {p.name for p in registry.prompts() if p.module == "inumet"}
    assert "inumet_comparar_estaciones" in names


def test_inumet_new_resource_registered():
    uris = {r.uri for r in registry.resources() if r.module == "inumet"}
    assert "uru://inumet/niveles-alerta" in uris


def test_inumet_comparar_estaciones_handler_references_tools():
    by_name = {p.name: p for p in registry.prompts()}
    text = by_name["inumet_comparar_estaciones"].handler(estaciones="Artigas, Rivera")
    assert isinstance(text, str)
    assert "inumet_estaciones" in text


def test_inumet_niveles_alerta_resource_handler():
    by_uri = {r.uri: r for r in registry.resources()}
    text = by_uri["uru://inumet/niveles-alerta"].handler()
    assert isinstance(text, str)
    assert "inumet_alertas" in text
    assert "inumet_pronostico" in text
