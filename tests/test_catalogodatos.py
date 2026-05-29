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
