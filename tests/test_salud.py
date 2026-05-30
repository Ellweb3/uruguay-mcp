"""Unit tests for the salud (health) module, with the HTTP layer mocked."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import uruguay_mcp.modules.salud  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.salud.constants import (
    ACTION_URL,
    MEDICAMENTOS_DATASET,
    POLICLINICAS_DATASET,
)
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


@respx.mock
async def test_buscar_defaults_to_group_salud():
    payload = {
        "success": True,
        "result": {
            "count": 1,
            "results": [
                {
                    "id": "abc",
                    "name": "vacunacion",
                    "title": "Actos vacunales",
                    "organization": {"title": "MSP"},
                    "groups": [{"title": "Salud"}],
                    "tags": [{"name": "vacunacion"}],
                    "num_resources": 1,
                    "resources": [
                        {
                            "id": "r1",
                            "name": "csv",
                            "format": "CSV",
                            "url": "http://x/r1.csv",
                            "datastore_active": True,
                        }
                    ],
                }
            ],
        },
    }
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("salud_buscar", {"q": "vacunacion", "rows": 5})

    assert route.called
    fq = dict(route.calls.last.request.url.params)["fq"]
    assert fq == "groups:salud"
    assert out["_meta"]["source"]["api"] == "catalogodatos.gub.uy"
    ds = out["data"]["results"][0]
    assert ds["organization"] == "MSP"
    assert ds["resources"][0]["datastore_active"] is True


@respx.mock
async def test_buscar_with_org_filter():
    payload = {"success": True, "result": {"count": 0, "results": []}}
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    await meta.call_tool("salud_buscar", {"org": "fondo-nacional-de-recursos"})

    fq = dict(route.calls.last.request.url.params)["fq"]
    assert "groups:salud" in fq
    assert "organization:fondo-nacional-de-recursos" in fq


@respx.mock
async def test_buscar_rejects_unknown_org():
    out = await meta.call_tool("salud_buscar", {"org": "intendencia-canelones"})
    assert out["error"]["code"] == "validation_error"


@respx.mock
async def test_second_identical_call_is_cached():
    payload = {"success": True, "result": {"count": 0, "results": []}}
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    first = await meta.call_tool("salud_buscar", {"q": "x"})
    second = await meta.call_tool("salud_buscar", {"q": "x"})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


@respx.mock
async def test_get_dataset_slims():
    payload = {
        "success": True,
        "result": {
            "id": "abc",
            "name": "egresos",
            "title": "Egresos hospitalarios",
            "organization": {"title": "MSP"},
            "groups": [{"title": "Salud"}],
            "resources": [
                {"id": "r1", "format": "CSV", "url": "u", "datastore_active": True}
            ],
        },
    }
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("salud_get_dataset", {"id": "egresos"})

    assert out["data"]["name"] == "egresos"
    assert out["data"]["resources"][0]["datastore_active"] is True


@respx.mock
async def test_get_dataset_not_found_becomes_error_envelope():
    payload = {"success": False, "error": {"message": "No encontrado"}}
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("salud_get_dataset", {"id": "nope"})
    assert out["error"]["code"] == "upstream_error"


@respx.mock
async def test_policlinicas_returns_csv_url_without_download():
    payload = {
        "success": True,
        "result": {
            "name": POLICLINICAS_DATASET,
            "title": "Ubicación de policlínicas",
            "organization": {"title": "Intendencia de Montevideo"},
            "resources": [
                {
                    "id": "r1",
                    "name": "policlinicas.csv",
                    "format": "CSV",
                    "url": "http://x/policlinicas.csv",
                    "datastore_active": False,
                }
            ],
        },
    }
    route = respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("salud_policlinicas", {})

    assert route.called
    assert out["data"]["csv_url"] == "http://x/policlinicas.csv"
    assert out["data"]["datastore_active"] is False
    assert "records" not in out["data"]


@respx.mock
async def test_policlinicas_downloads_and_parses_csv():
    pkg = {
        "success": True,
        "result": {
            "name": POLICLINICAS_DATASET,
            "title": "Ubicación de policlínicas",
            "organization": {"title": "IM"},
            "resources": [
                {
                    "id": "r1",
                    "format": "CSV",
                    "url": "http://x/policlinicas.csv",
                    "datastore_active": False,
                }
            ],
        },
    }
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=pkg)
    )
    csv_body = "nombre,barrio\nPoliclínica Centro,Centro\nPoliclínica Sur,Sur\n"
    respx.get("http://x/policlinicas.csv").mock(
        return_value=httpx.Response(200, text=csv_body)
    )

    out = await meta.call_tool("salud_policlinicas", {"download": True})

    assert out["data"]["count"] == 2
    assert out["data"]["fields"] == ["nombre", "barrio"]
    assert out["data"]["records"][0]["nombre"] == "Policlínica Centro"


@respx.mock
async def test_medicamentos_picks_latest_datastore_resource_and_filters():
    pkg = {
        "success": True,
        "result": {
            "name": MEDICAMENTOS_DATASET,
            "title": "Gasto por tratamientos",
            "resources": [
                {
                    "id": "old",
                    "format": "CSV",
                    "datastore_active": True,
                    "last_modified": "2017-01-01",
                },
                {
                    "id": "new",
                    "format": "CSV",
                    "datastore_active": True,
                    "last_modified": "2020-01-01",
                },
                {"id": "xml", "format": "XML", "datastore_active": False},
            ],
        },
    }
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=pkg)
    )
    ds = {
        "success": True,
        "result": {
            "total": 1,
            "fields": [{"id": "Anio", "type": "numeric"}],
            "records": [{"Anio": 2020, "Prestacion": "X"}],
        },
    }
    route = respx.get(f"{ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json=ds)
    )

    out = await meta.call_tool(
        "salud_medicamentos", {"anio": 2020, "area": "Montevideo", "q": "X"}
    )

    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["resource_id"] == "new"  # latest by last_modified
    assert params["q"] == "X"
    filters = json.loads(params["filters"])
    assert filters["Anio"] == 2020
    assert filters["Area_prestacion"] == "Montevideo"
    assert out["data"]["resource_id"] == "new"
    assert out["data"]["total"] == 1


@respx.mock
async def test_medicamentos_sql_aggregation():
    pkg = {
        "success": True,
        "result": {
            "name": MEDICAMENTOS_DATASET,
            "resources": [
                {"id": "rid", "format": "CSV", "datastore_active": True}
            ],
        },
    }
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=pkg)
    )
    sql_payload = {
        "success": True,
        "result": {
            "sql": 'SELECT "Area_prestacion" FROM "rid"',
            "fields": [{"id": "Area_prestacion", "type": "text"}],
            "records": [{"Area_prestacion": "Montevideo", "count": 5}],
        },
    }
    route = respx.get(f"{ACTION_URL}/datastore_search_sql").mock(
        return_value=httpx.Response(200, json=sql_payload)
    )

    out = await meta.call_tool(
        "salud_medicamentos",
        {"sql": 'SELECT "Area_prestacion", count(*) FROM "rid" GROUP BY "Area_prestacion"'},
    )

    assert route.called
    assert out["data"]["resource_id"] == "rid"
    assert out["data"]["records"][0]["Area_prestacion"] == "Montevideo"


@respx.mock
async def test_medicamentos_no_datastore_resource_errors():
    pkg = {
        "success": True,
        "result": {
            "name": MEDICAMENTOS_DATASET,
            "resources": [{"id": "pdf", "format": "PDF", "datastore_active": False}],
        },
    }
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=pkg)
    )

    out = await meta.call_tool("salud_medicamentos", {})
    assert out["error"]["code"] == "not_found"


@respx.mock
async def test_datastore_query_search():
    payload = {
        "success": True,
        "result": {
            "total": 3,
            "fields": [{"id": "x", "type": "text"}],
            "records": [{"_id": 1, "x": "a"}],
        },
    }
    route = respx.get(f"{ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool(
        "salud_datastore_query",
        {"resource_id": "rid", "q": "a", "filters": {"x": "a"}, "limit": 10},
    )

    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["resource_id"] == "rid"
    assert json.loads(params["filters"])["x"] == "a"
    assert out["data"]["total"] == 3


@respx.mock
async def test_datastore_query_sql():
    payload = {
        "success": True,
        "result": {
            "sql": 'SELECT * FROM "rid" LIMIT 1',
            "fields": [{"id": "x", "type": "int4"}],
            "records": [{"x": 7}],
        },
    }
    route = respx.get(f"{ACTION_URL}/datastore_search_sql").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool(
        "salud_datastore_query",
        {"resource_id": "rid", "sql": 'SELECT * FROM "rid" LIMIT 1'},
    )

    assert route.called
    assert out["data"]["records"][0]["x"] == 7


@respx.mock
async def test_datastore_query_sql_guard_rejects_non_select():
    route = respx.get(f"{ACTION_URL}/datastore_search_sql").mock(
        return_value=httpx.Response(200, json={"success": True, "result": {}})
    )

    out = await meta.call_tool(
        "salud_datastore_query",
        {"resource_id": "rid", "sql": 'DROP TABLE "rid"'},
    )

    assert out["error"]["code"] == "validation_error"
    assert not route.called


def test_module_prompts_registered_and_reference_real_tools():
    by_name = {p.name: p for p in registry.prompts() if p.module == "salud"}
    assert {
        "salud_buscar_datos",
        "salud_consultar_medicamentos",
        "salud_explorar_recurso",
    } <= set(by_name)
    assert "salud_buscar" in by_name["salud_buscar_datos"].handler(tema="vacunas")
    assert "salud_medicamentos" in by_name["salud_consultar_medicamentos"].handler()
    assert "salud_datastore_query" in by_name["salud_explorar_recurso"].handler(
        resource_id="rid"
    )


def test_module_resources_registered():
    uris = {r.uri for r in registry.resources() if r.module == "salud"}
    assert {
        "uru://salud/guia-de-uso",
        "uru://salud/fuentes",
    } <= uris
