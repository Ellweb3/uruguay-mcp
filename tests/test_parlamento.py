"""Unit tests for the Parlamento del Uruguay module, with HTTP mocked."""

from __future__ import annotations

import httpx
import pytest
import respx

import uruguay_mcp.modules.parlamento  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.parlamento.constants import ACTION_URL, ORG_SLUG
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


def _pkg_with_resources() -> dict:
    return {
        "id": "uuid-pkg",
        "name": "parlamento-del-uruguay-asistencias-a-la-camara-de-representantes",
        "title": "Asistencias a la Cámara de Representantes",
        "notes": "desc",
        "organization": {"title": "Parlamento del Uruguay"},
        "num_resources": 3,
        "metadata_modified": "2026-01-01",
        "resources": [
            {
                "id": "res-49",
                "name": "Asistencias - Legislatura 49",
                "format": "CSV",
                "url": "http://x/49.csv",
                "datastore_active": True,
            },
            {
                "id": "res-50",
                "name": "Asistencias - Legislatura 50",
                "format": "CSV",
                "url": "http://x/50.csv",
                "datastore_active": True,
            },
            {
                "id": "res-meta",
                "name": "Metadatos",
                "format": "CSV",
                "url": "http://x/meta.csv",
                "datastore_active": False,
            },
        ],
    }


@respx.mock
async def test_buscar_injects_org_and_slims():
    payload = {
        "success": True,
        "result": {"count": 1, "results": [_pkg_with_resources()]},
    }
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("parlamento_buscar", {"query": "asistencias", "rows": 5})

    assert route.called
    sent = route.calls.last.request
    assert f"organization%3A{ORG_SLUG}" in str(sent.url) or f"organization:{ORG_SLUG}" in str(
        sent.url
    )
    assert out["_meta"]["source"]["api"] == "catalogodatos.gub.uy"
    body = out["data"]
    assert body["count"] == 1
    ds = body["results"][0]
    assert ds["organization"] == "Parlamento del Uruguay"
    assert ds["resources"][1]["datastore_active"] is True


@respx.mock
async def test_get_dataset_slims():
    payload = {"success": True, "result": _pkg_with_resources()}
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool(
        "parlamento_get_dataset",
        {"id": "parlamento-del-uruguay-asistencias-a-la-camara-de-representantes"},
    )
    assert out["data"]["name"].startswith("parlamento-del-uruguay-asistencias")
    assert len(out["data"]["resources"]) == 3


@respx.mock
async def test_asistencias_defaults_to_latest_legislatura():
    show = {"success": True, "result": _pkg_with_resources()}
    ds = {
        "success": True,
        "result": {
            "total": 2,
            "fields": [{"id": "Fecha", "type": "text"}],
            "records": [{"Fecha": "2025-03-01"}],
        },
    }
    show_route = respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=show)
    )
    ds_route = respx.get(f"{ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json=ds)
    )

    out = await meta.call_tool("parlamento_asistencias", {"camara": "representantes"})

    assert show_route.called and ds_route.called
    # res-50 is the most recent active legislatura -> chosen by default.
    assert "resource_id=res-50" in str(ds_route.calls.last.request.url)
    assert out["data"]["legislatura"] == 50
    assert out["data"]["resource_id"] == "res-50"
    assert out["data"]["total"] == 2


@respx.mock
async def test_asistencias_specific_legislatura():
    show = {"success": True, "result": _pkg_with_resources()}
    ds = {"success": True, "result": {"total": 0, "fields": [], "records": []}}
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=show)
    )
    ds_route = respx.get(f"{ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json=ds)
    )

    out = await meta.call_tool(
        "parlamento_asistencias", {"camara": "representantes", "legislatura": 49}
    )
    assert "resource_id=res-49" in str(ds_route.calls.last.request.url)
    assert out["data"]["legislatura"] == 49


@respx.mock
async def test_asistencias_unknown_legislatura_is_not_found():
    show = {"success": True, "result": _pkg_with_resources()}
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=show)
    )

    out = await meta.call_tool(
        "parlamento_asistencias", {"camara": "representantes", "legislatura": 12}
    )
    assert out["error"]["code"] == "not_found"


async def test_asistencias_invalid_camara_is_validation_error():
    out = await meta.call_tool("parlamento_asistencias", {"camara": "diputados-mal"})
    assert out["error"]["code"] == "validation_error"


@respx.mock
async def test_second_identical_call_is_cached():
    payload = {"success": True, "result": {"count": 0, "results": []}}
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    first = await meta.call_tool("parlamento_buscar", {"query": "x"})
    second = await meta.call_tool("parlamento_buscar", {"query": "x"})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


@respx.mock
async def test_ckan_failure_becomes_error_envelope():
    payload = {"success": False, "error": {"message": "boom"}}
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("parlamento_get_dataset", {"id": "nope"})
    assert out["error"]["code"] == "upstream_error"


def test_module_prompts_registered():
    names = {p.name for p in registry.prompts() if p.module == "parlamento"}
    assert {
        "parlamento_buscar_datos",
        "parlamento_asistencias_legislatura",
        "parlamento_actividades_agenda",
    } <= names


def test_module_resources_registered():
    uris = {r.uri for r in registry.resources() if r.module == "parlamento"}
    assert {
        "uru://parlamento/guia-de-uso",
        "uru://parlamento/legislaturas",
    } <= uris


def test_prompt_text_references_real_tools():
    by_name = {p.name: p for p in registry.prompts()}
    text = by_name["parlamento_buscar_datos"].handler(tema="leyes")
    assert "parlamento_buscar" in text
