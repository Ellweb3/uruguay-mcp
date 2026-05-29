"""Unit tests for the Montevideo module, with the HTTP layer mocked.

Covers both surfaces: the public CKAN portal and the OAuth2-secured transport
API. All tests run offline (no live network).
"""

from __future__ import annotations

import httpx
import pytest
import respx

import uruguay_mcp.modules.montevideo  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.montevideo.constants import (
    ACTION_URL,
    TOKEN_URL,
    TRANSPORT_BASE_URL,
)
from uruguay_mcp.shared import cache, http


@pytest.fixture(autouse=True)
async def _clean(monkeypatch):
    cache.clear()
    # Default: credentials present so transport tests can mint a token.
    monkeypatch.setenv("URUGUAY_MCP_MVD_CLIENT_ID", "cid")
    monkeypatch.setenv("URUGUAY_MCP_MVD_CLIENT_SECRET", "secret")
    yield
    cache.clear()
    await http.aclose()


# --- CKAN surface ---------------------------------------------------------
@respx.mock
async def test_search_datasets_slims_and_envelopes():
    payload = {
        "success": True,
        "result": {
            "count": 1,
            "results": [
                {
                    "id": "abc",
                    "name": "arbolado",
                    "title": "Arbolado Público",
                    "notes": "desc",
                    "organization": {"title": "Áreas Verdes"},
                    "groups": [{"title": "Ambiente"}],
                    "tags": [{"name": "arboles"}],
                    "num_resources": 1,
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

    out = await meta.call_tool(
        "montevideo_search_datasets", {"query": "arbolado", "rows": 5}
    )

    assert route.called
    assert out["_meta"]["source"]["api"] == "ckan.montevideo.gub.uy"
    assert out["_meta"]["cached"] is False
    body = out["data"]
    assert body["count"] == 1
    ds = body["results"][0]
    assert ds["organization"] == "Áreas Verdes"
    assert ds["resources"][0]["datastore_active"] is True


@respx.mock
async def test_second_identical_call_is_cached():
    payload = {"success": True, "result": {"count": 0, "results": []}}
    route = respx.get(f"{ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    first = await meta.call_tool("montevideo_search_datasets", {"query": "x"})
    second = await meta.call_tool("montevideo_search_datasets", {"query": "x"})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


@respx.mock
async def test_ckan_failure_becomes_error_envelope():
    payload = {"success": False, "error": {"message": "boom"}}
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("montevideo_get_dataset", {"id": "nope"})
    assert out["error"]["code"] == "upstream_error"


@respx.mock
async def test_multas_transito_groups_and_filters_by_year():
    payload = {
        "success": True,
        "result": {
            "title": "Multas de tránsito",
            "name": "multas-de-transito",
            "notes": "Multas SUCIVE en Montevideo.",
            "metadata_modified": "2025-02-21",
            "resources": [
                {"id": "a", "name": "Tipos de vehículo", "format": "CSV", "url": "http://x/a"},
                {"id": "b", "name": "Multas SUCIVE 2017", "format": "CSV ZIP", "url": "http://x/b"},
                {"id": "c", "name": "Multas SUCIVE 2018", "format": "CSV ZIP", "url": "http://x/c"},
            ],
        },
    }
    respx.get(f"{ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("montevideo_multas_transito", {"year": 2018})
    body = out["data"]
    assert out["_meta"]["source"]["api"] == "ckan.montevideo.gub.uy"
    # Reference table (no year) is separated from annual files.
    assert [r["name"] for r in body["reference_tables"]] == ["Tipos de vehículo"]
    # Year filter keeps only 2018.
    assert len(body["annual_files"]) == 1
    assert body["annual_files"][0]["years"] == [2018]
    assert "deuda por vehículo" in body["note"]


# --- Transport surface ----------------------------------------------------
@respx.mock
async def test_bus_eta_mints_token_and_envelopes():
    token = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "tok-123"})
    )
    eta_payload = [
        {
            "busId": 7,
            "line": "103",
            "lineVariantId": 55,
            "origin": "Pocitos",
            "destination": "Centro",
            "subline": "",
            "eta": 240,
            "distance": 1200,
            "location": {"type": "Point", "coordinates": [-56.16, -34.9]},
            "companyName": "CUTCSA",
            "access": True,
        }
    ]
    eta = respx.get(
        f"{TRANSPORT_BASE_URL}/buses/busstops/123/upcomingbuses"
    ).mock(return_value=httpx.Response(200, json=eta_payload))

    out = await meta.call_tool(
        "montevideo_bus_eta", {"busstop_id": 123, "lines": ["103", "104"]}
    )

    assert token.called
    assert eta.called
    # Bearer header was sent on the protected call.
    assert eta.calls.last.request.headers["authorization"] == "Bearer tok-123"
    # The mandatory comma-separated lines param was forwarded.
    assert b"lines=103%2C104" in eta.calls.last.request.url.query
    assert out["_meta"]["source"]["api"] == "api.montevideo.gub.uy/transportepublico"
    item = out["data"][0]
    assert item["line"] == "103"
    assert item["eta"] == 240


@respx.mock
async def test_buses_near_passes_center_and_radius():
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "tok"})
    )
    geo = respx.get(f"{TRANSPORT_BASE_URL}/buses/geo").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "line": "60"}])
    )

    out = await meta.call_tool(
        "montevideo_buses_near", {"lat": -34.9, "lng": -56.16, "radius_m": 500}
    )

    assert geo.called
    q = geo.calls.last.request.url.query
    assert b"center=-34.9%2C-56.16" in q
    assert b"radius=500" in q
    assert out["data"][0]["line"] == "60"


@respx.mock
async def test_list_busstops_client_side_filter():
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "tok"})
    )
    stops = [
        {"busstopId": 1, "street1": "18 de Julio", "street2": "Ejido"},
        {"busstopId": 2, "street1": "Rivera", "street2": "Comercio"},
    ]
    respx.get(f"{TRANSPORT_BASE_URL}/buses/busstops").mock(
        return_value=httpx.Response(200, json=stops)
    )

    out = await meta.call_tool("montevideo_list_busstops", {"query": "rivera"})
    data = out["data"]
    assert len(data) == 1
    assert data[0]["busstopId"] == 2


async def test_transport_without_credentials_is_typed_error(monkeypatch):
    monkeypatch.delenv("URUGUAY_MCP_MVD_CLIENT_ID", raising=False)
    monkeypatch.delenv("URUGUAY_MCP_MVD_CLIENT_SECRET", raising=False)

    out = await meta.call_tool(
        "montevideo_bus_eta", {"busstop_id": 1, "lines": ["103"]}
    )
    assert out["error"]["code"] == "validation_error"


async def test_bus_eta_requires_at_least_one_line():
    out = await meta.call_tool(
        "montevideo_bus_eta", {"busstop_id": 1, "lines": []}
    )
    assert out["error"]["code"] == "validation_error"


# --- Prompts & resources --------------------------------------------------
def test_prompts_registered():
    from uruguay_mcp.shared.registry import registry

    by_name = {p.name: p for p in registry.prompts()}
    expected = {
        "montevideo_proximo_bus",
        "montevideo_buses_cercanos",
        "montevideo_multas_resumen",
    }
    assert expected <= set(by_name)
    for name in expected:
        spec = by_name[name]
        assert spec.module == "montevideo"
        assert spec.description


def test_resources_registered():
    from uruguay_mcp.shared.registry import registry

    by_uri = {r.uri: r for r in registry.resources()}
    expected = {
        "uru://montevideo/credenciales-transporte",
        "uru://montevideo/indice-datasets",
    }
    assert expected <= set(by_uri)
    for uri in expected:
        spec = by_uri[uri]
        assert spec.module == "montevideo"
        assert spec.mime_type == "text/markdown"


async def test_prompt_handlers_return_spanish_strings():
    from uruguay_mcp.shared.registry import registry

    by_name = {p.name: p for p in registry.prompts()}

    bus = by_name["montevideo_proximo_bus"].handler("18 de Julio y Ejido", "103")
    assert "montevideo_bus_eta" in bus

    near = by_name["montevideo_buses_cercanos"].handler(-34.9, -56.16, 500)
    assert "montevideo_buses_near" in near

    multas = by_name["montevideo_multas_resumen"].handler(2018)
    assert "montevideo_multas_transito" in multas
    assert "2018" in multas


def test_resource_handlers_return_markdown():
    from uruguay_mcp.shared.registry import registry

    by_uri = {r.uri: r for r in registry.resources()}

    creds = by_uri["uru://montevideo/credenciales-transporte"].handler()
    assert "URUGUAY_MCP_MVD_CLIENT_ID" in creds

    index = by_uri["uru://montevideo/indice-datasets"].handler()
    assert "montevideo_search_datasets" in index
