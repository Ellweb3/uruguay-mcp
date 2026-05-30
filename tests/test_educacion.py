"""Unit tests for the ANEP education module, with the HTTP layer mocked."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import uruguay_mcp.modules.educacion  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.educacion.constants import (
    ACTION_URL,
    DATASTORE_RESOURCES,
    DEFAULT_RESOURCE,
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
async def test_buscar_pins_org_and_slims():
    payload = {
        "success": True,
        "result": {
            "count": 2,
            "results": [
                {
                    "id": "uuid-1",
                    "name": "anep-centros-anep",
                    "title": "Centros Anep",
                    "notes": "desc",
                    "organization": {"title": "ANEP"},
                    "num_resources": 1,
                    "metadata_modified": "2021-01-01",
                    "resources": [
                        {
                            "id": "r-shape",
                            "name": "CENTROS_ANEP",
                            "format": "Shape",
                            "url": "http://sig.anep.edu.uy/SIGANEP/FORMATOS/CENTROS_ANEP.rar",
                            "datastore_active": False,
                        }
                    ],
                }
            ],
        },
    }
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("educacion_buscar", {"q": "centros", "rows": 5})

    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["fq"] == "organization:anep"
    assert out["_meta"]["source"]["api"] == "catalogodatos.gub.uy"
    body = out["data"]
    assert body["count"] == 2
    ds = body["results"][0]
    assert ds["organization"] == "ANEP"
    assert ds["resources"][0]["datastore_active"] is False


@respx.mock
async def test_buscar_empty_query_uses_wildcard():
    payload = {"success": True, "result": {"count": 0, "results": []}}
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    await meta.call_tool("educacion_buscar", {})

    params = dict(route.calls.last.request.url.params)
    assert params["q"] == "*:*"
    assert params["fq"] == "organization:anep"


@respx.mock
async def test_get_dataset_slims_resources():
    payload = {
        "success": True,
        "result": {
            "id": "uuid-oferta",
            "name": "anep-http-sig-anep-edu-uy-siganep-formatos",
            "title": "Oferta educativa de la ANEP",
            "organization": {"title": "ANEP"},
            "num_resources": 5,
            "resources": [
                {
                    "id": DEFAULT_RESOURCE,
                    "name": "CES",
                    "format": "XLSX",
                    "url": "https://sig.anep.edu.uy/SIGANEP/FORMATOS/CES.xlsx",
                    "datastore_active": True,
                }
            ],
        },
    }
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool(
        "educacion_get_dataset", {"id": "anep-http-sig-anep-edu-uy-siganep-formatos"}
    )

    assert out["data"]["title"] == "Oferta educativa de la ANEP"
    assert out["data"]["resources"][0]["datastore_active"] is True


@respx.mock
async def test_centros_default_queries_dges_datastore():
    payload = {
        "success": True,
        "result": {
            "total": 1010,
            "fields": [{"id": "Nombre", "type": "text"}],
            "records": [{"_id": 1, "Nombre": "Liceo 1", "Departamento": "MONTEVIDEO"}],
        },
    }
    route = respx.get(f"{ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool(
        "educacion_centros", {"departamento": "MONTEVIDEO", "limit": 5}
    )

    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["resource_id"] == DEFAULT_RESOURCE
    assert json.loads(params["filters"]) == {"Departamento": "MONTEVIDEO"}
    body = out["data"]
    assert body["mode"] == "datastore"
    assert body["total"] == 1010
    assert body["records"][0]["Nombre"] == "Liceo 1"


@respx.mock
async def test_centros_subsistema_picks_resource_and_q():
    payload = {"success": True, "result": {"total": 55, "fields": [], "records": []}}
    route = respx.get(f"{ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    await meta.call_tool("educacion_centros", {"subsistema": "789", "q": "ARTIGAS"})

    params = dict(route.calls.last.request.url.params)
    assert params["resource_id"] == DATASTORE_RESOURCES["789"]
    assert params["q"] == "ARTIGAS"


@respx.mock
async def test_centros_download_only_subsistema_returns_url():
    payload = {
        "success": True,
        "result": {
            "id": "uuid-oferta",
            "name": "anep-http-sig-anep-edu-uy-siganep-formatos",
            "resources": [
                {
                    "id": "d98bfe2f-1850-469e-b2a4-7c12c064e2f0",
                    "name": "CEIP",
                    "format": "XLSX",
                    "url": "https://sig.anep.edu.uy/SIGANEP/FORMATOS/CEIP.xlsx",
                    "datastore_active": False,
                }
            ],
        },
    }
    ds_route = respx.get(f"{ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    show_route = respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("educacion_centros", {"subsistema": "ceip"})

    # Download-only path must NOT hit datastore_search at all.
    assert not ds_route.called
    assert show_route.called
    body = out["data"]
    assert body["mode"] == "download"
    assert body["resource"]["url"].endswith("CEIP.xlsx")


@respx.mock
async def test_centros_inactive_datastore_falls_back_to_download():
    error_payload = {
        "success": False,
        "error": {"__type": "DatastoreEntityDoesNotExist", "message": "not found"},
    }
    pkg_payload = {
        "success": True,
        "result": {
            "id": "uuid-oferta",
            "resources": [
                {
                    "id": DEFAULT_RESOURCE,
                    "name": "CES",
                    "format": "XLSX",
                    "url": "https://sig.anep.edu.uy/SIGANEP/FORMATOS/CES.xlsx",
                    "datastore_active": False,
                }
            ],
        },
    }
    respx.get(f"{ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json=error_payload)
    )
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=pkg_payload)
    )

    out = await meta.call_tool("educacion_centros", {})

    body = out["data"]
    assert body["mode"] == "download"
    assert body["resource"]["url"].endswith("CES.xlsx")


@respx.mock
async def test_ckan_failure_becomes_error_envelope():
    payload = {"success": False, "error": {"message": "boom"}}
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("educacion_get_dataset", {"id": "nope"})
    assert out["error"]["code"] == "upstream_error"


@respx.mock
async def test_second_identical_call_is_cached():
    payload = {"success": True, "result": {"count": 0, "results": []}}
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    first = await meta.call_tool("educacion_buscar", {"q": "x"})
    second = await meta.call_tool("educacion_buscar", {"q": "x"})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


def test_module_prompts_registered():
    names = {p.name for p in registry.prompts() if p.module == "educacion"}
    assert {
        "educacion_explorar_anep",
        "educacion_centros_por_departamento",
    } <= names


def test_module_resources_registered():
    uris = {r.uri for r in registry.resources() if r.module == "educacion"}
    assert "uru://educacion/guia-de-uso" in uris


def test_prompt_text_references_real_tools():
    by_name = {p.name: p for p in registry.prompts()}
    text = by_name["educacion_explorar_anep"].handler(tema="liceos")
    assert "educacion_buscar" in text
    assert "educacion_get_dataset" in text
    text2 = by_name["educacion_centros_por_departamento"].handler()
    assert "educacion_centros" in text2
