"""Unit tests for the gubuy (State APIs/services) module, HTTP mocked."""

from __future__ import annotations

import httpx
import pytest
import respx

import uruguay_mcp.modules.gubuy  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.gubuy.constants import ACTION_URL
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


def _showcase(name: str, title: str, tags: list[str]) -> dict:
    return {
        "id": f"id-{name}",
        "name": name,
        "title": title,
        "notes": f"descripcion de {title}",
        "url": f"https://app/{name}",
        "author": "AGESIC",
        "tags": [{"name": t} for t in tags],
        "image_display_url": f"https://img/{name}.png",
        "num_datasets": 0,
        "metadata_modified": "2026-01-01",
        "showcase_notes_formatted": "<p>html</p>",
    }


@respx.mock
async def test_list_servicios_filters_and_envelopes():
    payload = {
        "success": True,
        "result": [
            _showcase("comprasestatales", "Compras Estatales", ["compras", "api"]),
            _showcase("transparencia", "Portal de Transparencia", ["transparencia"]),
        ],
    }
    route = respx.get(f"{ACTION_URL}/ckanext_showcase_list").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("gubuy_list_servicios", {"query": "compras"})

    assert route.called
    assert out["_meta"]["source"]["api"] == "catalogodatos.gub.uy/showcase"
    assert out["_meta"]["cached"] is False
    body = out["data"]
    assert body["count"] == 1
    sc = body["results"][0]
    assert sc["name"] == "comprasestatales"
    assert sc["url"] == "https://app/comprasestatales"
    assert sc["image_url"] == "https://img/comprasestatales.png"
    # HTML field must not leak into the slim projection.
    assert "showcase_notes_formatted" not in sc


@respx.mock
async def test_list_servicios_tag_filter():
    payload = {
        "success": True,
        "result": [
            _showcase("a", "Servicio A", ["transparencia"]),
            _showcase("b", "Servicio B", ["compras"]),
        ],
    }
    respx.get(f"{ACTION_URL}/ckanext_showcase_list").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("gubuy_list_servicios", {"tag": "compras"})
    body = out["data"]
    assert body["count"] == 1
    assert body["results"][0]["name"] == "b"


@respx.mock
async def test_get_servicio_slims():
    payload = {"success": True, "result": _showcase("x", "Servicio X", ["t1"])}
    route = respx.get(f"{ACTION_URL}/ckanext_showcase_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("gubuy_get_servicio", {"id": "x"})

    assert route.called
    assert out["data"]["title"] == "Servicio X"
    assert out["data"]["tags"] == ["t1"]


@respx.mock
async def test_servicio_datasets_empty_is_not_error():
    payload = {"success": True, "result": []}
    respx.get(f"{ACTION_URL}/ckanext_showcase_package_list").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("gubuy_servicio_datasets", {"showcase_id": "x"})
    assert out["data"]["count"] == 0
    assert out["data"]["results"] == []


@respx.mock
async def test_search_apis_uses_json_facet():
    payload = {
        "success": True,
        "result": {
            "count": 2253,
            "results": [
                {
                    "id": "d1",
                    "name": "buses",
                    "title": "Buses",
                    "notes": "n",
                    "organization": {"title": "IM"},
                    "tags": [{"name": "transporte"}],
                    "num_resources": 1,
                    "metadata_modified": "2026-01-01",
                    "resources": [
                        {"id": "r1", "name": "json", "format": "JSON", "url": "http://x"}
                    ],
                }
            ],
        },
    }
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("gubuy_search_apis", {"query": "buses", "rows": 5})

    assert route.called
    assert route.calls.last.request.url.params["fq"] == "res_format:JSON"
    body = out["data"]
    assert body["count"] == 2253
    assert body["results"][0]["organization"] == "IM"


@respx.mock
async def test_second_identical_call_is_cached():
    payload = {"success": True, "result": []}
    route = respx.get(f"{ACTION_URL}/ckanext_showcase_list").mock(
        return_value=httpx.Response(200, json=payload)
    )

    first = await meta.call_tool("gubuy_list_servicios", {})
    second = await meta.call_tool("gubuy_list_servicios", {})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


def test_gubuy_prompts_registered():
    by_name = {p.name: p for p in registry.prompts() if p.module == "gubuy"}
    assert {
        "gubuy_buscar_servicios",
        "gubuy_buscar_apis",
        "gubuy_fuentes_de_servicio",
    } <= set(by_name)
    # Handlers return ready-to-use Spanish strings referencing real tools.
    out = by_name["gubuy_buscar_servicios"].handler(tema="compras")
    assert "gubuy_list_servicios" in out
    assert "compras" in out
    assert by_name["gubuy_fuentes_de_servicio"].handler(servicio="X")
    assert "gubuy_search_apis" in by_name["gubuy_buscar_apis"].handler()


def test_gubuy_resources_registered():
    by_uri = {r.uri: r for r in registry.resources() if r.module == "gubuy"}
    assert "uru://gubuy/guia-catalogo" in by_uri
    assert "uru://gubuy/etiquetas-frecuentes" in by_uri
    guia = by_uri["uru://gubuy/guia-catalogo"]
    assert guia.mime_type == "text/markdown"
    body = guia.handler()
    assert "gubuy_list_servicios" in body
    assert "gubuy_search_apis" in body


@respx.mock
async def test_ckan_failure_becomes_error_envelope():
    payload = {"success": False, "error": {"message": "boom"}}
    respx.get(f"{ACTION_URL}/ckanext_showcase_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("gubuy_get_servicio", {"id": "nope"})
    assert out["error"]["code"] == "upstream_error"
