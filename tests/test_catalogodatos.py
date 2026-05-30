"""Unit tests for the CKAN catalog module, with the HTTP layer mocked."""

from __future__ import annotations

import httpx
import pytest
import respx

import uruguay_mcp.modules.catalogodatos  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.catalogodatos.constants import ACTION_URL
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


@respx.mock
async def test_search_datasets_slims_and_envelopes():
    payload = {
        "success": True,
        "result": {
            "count": 1,
            "results": [
                {
                    "id": "abc",
                    "name": "indicadores-salud",
                    "title": "Indicadores de Salud",
                    "notes": "desc",
                    "organization": {"title": "MSP"},
                    "groups": [{"title": "Salud"}],
                    "tags": [{"name": "salud"}],
                    "num_resources": 2,
                    "metadata_modified": "2026-01-01",
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

    out = await meta.call_tool("catalogo_search_datasets", {"query": "salud", "rows": 5})

    assert route.called
    assert out["_meta"]["source"]["api"] == "catalogodatos.gub.uy"
    assert out["_meta"]["cached"] is False
    body = out["data"]
    assert body["count"] == 1
    ds = body["results"][0]
    assert ds["organization"] == "MSP"
    assert ds["resources"][0]["datastore_active"] is True


@respx.mock
async def test_second_identical_call_is_cached():
    payload = {"success": True, "result": {"count": 0, "results": []}}
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    first = await meta.call_tool("catalogo_search_datasets", {"query": "x"})
    second = await meta.call_tool("catalogo_search_datasets", {"query": "x"})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1  # second served from cache


@respx.mock
async def test_ckan_failure_becomes_error_envelope():
    payload = {"success": False, "error": {"message": "boom"}}
    respx.get(f"{ACTION_URL}/package_show").mock(return_value=httpx.Response(200, json=payload))

    out = await meta.call_tool("catalogo_get_dataset", {"id": "nope"})
    assert out["error"]["code"] == "upstream_error"


def test_module_prompts_registered():
    names = {p.name for p in registry.prompts() if p.module == "catalogodatos"}
    assert {
        "catalogo_buscar_por_tema",
        "catalogo_explorar_organizaciones",
        "catalogo_consultar_datastore",
    } <= names


def test_module_resources_registered():
    uris = {r.uri for r in registry.resources() if r.module == "catalogodatos"}
    assert {
        "uru://catalogodatos/guia-de-uso",
        "uru://catalogodatos/categorias",
    } <= uris


def test_prompt_text_references_real_tools():
    by_name = {p.name: p for p in registry.prompts()}
    text = by_name["catalogo_buscar_por_tema"].handler(tema="salud")
    assert "catalogo_search_datasets" in text


@respx.mock
async def test_datastore_sql_returns_records():
    payload = {
        "success": True,
        "result": {
            "sql": 'SELECT * FROM "r1" LIMIT 1',
            "fields": [{"id": "x", "type": "int4"}],
            "records": [{"_id": 1, "x": 7}],
        },
    }
    route = respx.get(f"{ACTION_URL}/datastore_search_sql").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool(
        "catalogo_datastore_sql", {"sql": 'SELECT * FROM "r1" LIMIT 1'}
    )

    assert route.called
    assert out["_meta"]["source"]["api"] == "catalogodatos.gub.uy"
    assert out["data"]["records"][0]["x"] == 7
    assert out["data"]["fields"][0]["id"] == "x"


@respx.mock
async def test_datastore_sql_guard_rejects_non_select():
    route = respx.get(f"{ACTION_URL}/datastore_search_sql").mock(
        return_value=httpx.Response(200, json={"success": True, "result": {}})
    )

    out = await meta.call_tool(
        "catalogo_datastore_sql", {"sql": 'DROP TABLE "r1"'}
    )

    assert out["error"]["code"] == "validation_error"
    assert not route.called  # guard short-circuits before any HTTP call


@respx.mock
async def test_datastore_sql_guard_rejects_multi_statement():
    route = respx.get(f"{ACTION_URL}/datastore_search_sql").mock(
        return_value=httpx.Response(200, json={"success": True, "result": {}})
    )

    out = await meta.call_tool(
        "catalogo_datastore_sql",
        {"sql": 'SELECT * FROM "r1"; SELECT 1'},
    )

    assert out["error"]["code"] == "validation_error"
    assert not route.called


@respx.mock
async def test_list_tags_filters_and_slices():
    payload = {"success": True, "result": ["salud", "Salud", "salud-mental", "educacion"]}
    route = respx.get(f"{ACTION_URL}/tag_list").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("catalogo_list_tags", {"query": "salud", "limit": 2})

    assert route.called
    # 'limit' must not be sent upstream (CKAN ignores it); slice happens client-side.
    assert "limit" not in dict(route.calls.last.request.url.params)
    assert out["data"]["count"] == 2
    assert out["data"]["tags"] == ["salud", "Salud"]


@respx.mock
async def test_recent_datasets_sorts_by_modified():
    payload = {
        "success": True,
        "result": {
            "count": 2680,
            "results": [
                {"id": "a", "name": "nuevo", "title": "Nuevo", "metadata_modified": "2026-05-01"}
            ],
        },
    }
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("catalogo_recent_datasets", {"limit": 5})

    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["sort"] == "metadata_modified desc"
    assert out["data"]["count"] == 2680
    assert out["data"]["results"][0]["name"] == "nuevo"


@respx.mock
async def test_resource_show_slims():
    payload = {
        "success": True,
        "result": {
            "id": "r1",
            "name": "datos.csv",
            "format": "CSV",
            "url": "http://x/r1.csv",
            "datastore_active": True,
            "package_id": "pkg1",
            "size": 1234,
        },
    }
    respx.get(f"{ACTION_URL}/resource_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("catalogo_resource_show", {"resource_id": "r1"})

    assert out["data"]["datastore_active"] is True
    assert out["data"]["format"] == "CSV"
    assert out["data"]["package_id"] == "pkg1"


@respx.mock
async def test_resource_show_not_found_becomes_error_envelope():
    payload = {"success": False, "error": {"__type": "Not Found Error", "message": "No encontrado"}}
    respx.get(f"{ACTION_URL}/resource_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("catalogo_resource_show", {"resource_id": "missing"})
    assert out["error"]["code"] == "upstream_error"


def test_new_prompt_registered_and_references_real_tools():
    by_name = {p.name: p for p in registry.prompts()}
    assert "catalogo_sql_consulta" in by_name
    text = by_name["catalogo_sql_consulta"].handler(resource_id="r1")
    assert "catalogo_datastore_sql" in text
    assert "catalogo_resource_show" in text
