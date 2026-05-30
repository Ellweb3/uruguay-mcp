"""Unit tests for the MIDES module, with the HTTP layer mocked."""

from __future__ import annotations

import httpx
import pytest
import respx

import uruguay_mcp.modules.mides  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.mides.constants import CKAN_ACTION_URL, GUIA_SEARCH_URL
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry

GUIA_HTML = """<html><body>
  <div class="result">
    <a href="https://guiaderecursos.mides.gub.uy/27548/servicios-de-atencion">
      Servicios de atención a mujeres
    </a>
    <div class="desc">Atención en situación de violencia.</div>
  </div>
  <div class="result">
    <a href="https://guiaderecursos.mides.gub.uy/27600/centro-de-dia-vejez">
      Centro de día para personas mayores
    </a>
  </div>
</body></html>
"""


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


@respx.mock
async def test_buscar_forces_org_filter_and_slims():
    payload = {
        "success": True,
        "result": {
            "count": 1875,
            "results": [
                {
                    "id": "abc",
                    "name": "mides-indicador-10053",
                    "title": "Tarjetas Uruguay Social (TUS)",
                    "notes": "Evolución mensual",
                    "organization": {"title": "MIDES"},
                    "groups": [{"title": "Estadísticos"}],
                    "tags": [{"name": "tus"}],
                    "num_resources": 4,
                    "metadata_modified": "2026-01-01",
                    "resources": [
                        {
                            "id": "r1",
                            "name": "Datos",
                            "format": "CSV",
                            "url": "http://x/r1.csv",
                            "datastore_active": True,
                        }
                    ],
                }
            ],
        },
    }
    route = respx.get(f"{CKAN_ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("mides_buscar", {"query": "tarjeta uruguay social", "rows": 5})

    assert route.called
    assert route.calls.last.request.url.params["fq"] == "organization:mides"
    assert out["_meta"]["source"]["api"] == "catalogodatos.gub.uy"
    assert out["_meta"]["cached"] is False
    body = out["data"]
    assert body["count"] == 1875
    ds = body["results"][0]
    assert ds["organization"] == "MIDES"
    assert ds["groups"] == ["Estadísticos"]
    assert ds["resources"][0]["datastore_active"] is True


@respx.mock
async def test_buscar_second_call_is_cached():
    payload = {"success": True, "result": {"count": 0, "results": []}}
    route = respx.get(f"{CKAN_ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    first = await meta.call_tool("mides_buscar", {"query": "x"})
    second = await meta.call_tool("mides_buscar", {"query": "x"})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


@respx.mock
async def test_get_dataset_slims():
    payload = {
        "success": True,
        "result": {
            "id": "abc",
            "name": "mides-indicador-10053",
            "title": "TUS",
            "num_resources": 1,
            "resources": [
                {
                    "id": "r1",
                    "format": "JSON",
                    "url": "http://x/r1.json",
                    "datastore_active": True,
                }
            ],
        },
    }
    respx.get(f"{CKAN_ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("mides_get_dataset", {"id": "mides-indicador-10053"})

    assert out["data"]["name"] == "mides-indicador-10053"
    assert out["data"]["resources"][0]["datastore_active"] is True


@respx.mock
async def test_get_dataset_not_found_maps_to_not_found_error():
    payload = {
        "success": False,
        "error": {"__type": "Not Found Error", "message": "Not found"},
    }
    respx.get(f"{CKAN_ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("mides_get_dataset", {"id": "missing"})
    assert out["error"]["code"] == "not_found"


@respx.mock
async def test_buscar_ckan_failure_is_upstream_error():
    payload = {"success": False, "error": {"message": "boom"}}
    respx.get(f"{CKAN_ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("mides_buscar", {"query": "x"})
    assert out["error"]["code"] == "upstream_error"


@respx.mock
async def test_serie_returns_records_and_passes_sort():
    payload = {
        "success": True,
        "result": {
            "total": 108,
            "fields": [
                {"id": "_id", "type": "int4"},
                {"id": "Meses", "type": "text"},
                {"id": "año", "type": "int4"},
                {"id": "valor", "type": "numeric"},
            ],
            "records": [{"_id": 1, "Meses": "Enero", "año": 2010, "valor": 87392}],
        },
    }
    route = respx.get(f"{CKAN_ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool(
        "mides_serie",
        {"resource_id": "f966f4e7", "limit": 5, "sort": "año desc"},
    )

    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["resource_id"] == "f966f4e7"
    assert params["sort"] == "año desc"
    body = out["data"]
    assert body["total"] == 108
    assert body["records"][0]["valor"] == 87392


@respx.mock
async def test_serie_not_found_maps_to_not_found_error():
    payload = {
        "success": False,
        "error": {"__type": "Not Found Error", "message": "Not found"},
    }
    respx.get(f"{CKAN_ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("mides_serie", {"resource_id": "bad"})
    assert out["error"]["code"] == "not_found"


@respx.mock
async def test_recursos_scrapes_canonical_links():
    route = respx.get(GUIA_SEARCH_URL).mock(
        return_value=httpx.Response(200, text=GUIA_HTML)
    )

    out = await meta.call_tool("mides_recursos", {"query": "violencia"})

    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["cmdaction"] == "search"
    assert params["query"] == "violencia"
    assert out["_meta"]["source"]["api"] == "guiaderecursos.mides.gub.uy"
    body = out["data"]
    assert body["count"] == 2
    first = body["results"][0]
    assert first["id"] == "27548"
    assert first["url"].endswith("/27548/servicios-de-atencion")
    assert "mujeres" in first["title"].lower()


@respx.mock
async def test_recursos_passes_area_and_poblacion_facets():
    route = respx.get(GUIA_SEARCH_URL).mock(
        return_value=httpx.Response(200, text=GUIA_HTML)
    )

    await meta.call_tool(
        "mides_recursos", {"query": "vejez", "area": 15, "poblacion": 5}
    )

    params = dict(route.calls.last.request.url.params)
    assert params["area"] == "15"
    assert params["poblacion"] == "5"


@respx.mock
async def test_recursos_degrades_gracefully_on_empty_html():
    respx.get(GUIA_SEARCH_URL).mock(
        return_value=httpx.Response(200, text="<html><body>sin enlaces</body></html>")
    )

    out = await meta.call_tool("mides_recursos", {"query": "nada"})

    body = out["data"]
    assert body["count"] == 0
    assert "fallback" in body
    assert body["fallback"]["guia_url"].startswith("https://guiaderecursos.mides.gub.uy")


def test_module_prompts_registered():
    names = {p.name for p in registry.prompts() if p.module == "mides"}
    assert {
        "mides_evolucion_prestacion",
        "mides_buscar_prestaciones",
        "mides_donde_acudir",
    } <= names


def test_module_resources_registered():
    uris = {r.uri for r in registry.resources() if r.module == "mides"}
    assert {
        "uru://mides/guia-de-uso",
        "uru://mides/guia-recursos",
    } <= uris


def test_prompt_text_references_real_tools():
    by_name = {p.name: p for p in registry.prompts()}
    text = by_name["mides_evolucion_prestacion"].handler(prestacion="TUS")
    assert "mides_buscar" in text
    assert "mides_get_dataset" in text
    assert "mides_serie" in text
