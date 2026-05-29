"""Unit tests for the INE (ANDA/NADA + CKAN) module, with HTTP mocked."""

from __future__ import annotations

import httpx
import pytest
import respx

import uruguay_mcp.modules.ine  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.ine.constants import (
    ANDA_CATALOG_URL,
    ANDA_SEARCH_URL,
    CKAN_ACTION_URL,
    MODULE,
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
async def test_search_studies_slims_and_surfaces_idno():
    payload = {
        "result": {
            "found": 1,
            "total": 389,
            "limit": 5,
            "offset": 0,
            "rows": [
                {
                    "id": 123,
                    "idno": "URY-INE-ECH-2023-v01",
                    "title": "Encuesta Continua de Hogares 2023",
                    "nation": "Uruguay",
                    "authoring_entity": "INE",
                    "form_model": "data_na",
                    "year_start": "2023",
                    "year_end": "2023",
                    "repo_title": "Inventario de Operaciones Estadísticas",
                    "total_views": 10,
                    "total_downloads": 2,
                    "url": "https://www4.ine.gub.uy/Anda5/index.php/catalog/123",
                }
            ],
        }
    }
    route = respx.get(ANDA_SEARCH_URL).mock(return_value=httpx.Response(200, json=payload))

    out = await meta.call_tool("ine_search_studies", {"query": "hogares", "rows": 5})

    assert route.called
    assert out["_meta"]["source"]["api"] == "ine.gub.uy"
    assert out["_meta"]["cached"] is False
    body = out["data"]
    assert body["found"] == 1
    assert body["total"] == 389
    row = body["results"][0]
    # idno (the URY-...-vNN string) must be surfaced for study-detail lookups.
    assert row["idno"] == "URY-INE-ECH-2023-v01"
    assert row["id"] == 123
    assert row["authoring_entity"] == "INE"


@respx.mock
async def test_search_studies_cache():
    payload = {"result": {"found": 0, "total": 389, "limit": 20, "offset": 0, "rows": []}}
    route = respx.get(ANDA_SEARCH_URL).mock(return_value=httpx.Response(200, json=payload))

    first = await meta.call_tool("ine_search_studies", {"query": "z"})
    second = await meta.call_tool("ine_search_studies", {"query": "z"})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


@respx.mock
async def test_get_study_by_idno():
    idno = "URY-INE-ECH-2023-v01"
    payload = {
        "status": "success",
        "dataset": {
            "id": 123,
            "idno": idno,
            "type": "survey",
            "title": "Encuesta Continua de Hogares 2023",
            "nation": "Uruguay",
            "authoring_entity": "INE",
            "year_start": "2023",
            "year_end": "2023",
            "varcount": 500,
            "published": 1,
            "data_access_type": "open",
            "remote_data_url": "https://example.org/data",
            "link_questionnaire": "https://example.org/q.pdf",
            "metadata": {"doc_desc": {}, "study_desc": {}},
        },
    }
    route = respx.get(f"{ANDA_CATALOG_URL}/{idno}").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("ine_get_study", {"idno": idno})

    assert route.called
    assert out["_meta"]["source"]["api"] == "ine.gub.uy"
    body = out["data"]
    assert body["idno"] == idno
    assert body["type"] == "survey"
    assert body["data_access_type"] == "open"
    assert body["metadata"] == {"doc_desc": {}, "study_desc": {}}


@respx.mock
async def test_get_study_idno_not_found_becomes_error():
    payload = {"status": "failed", "message": "IDNO-NOT-FOUND"}
    respx.get(f"{ANDA_CATALOG_URL}/999").mock(return_value=httpx.Response(400, json=payload))

    out = await meta.call_tool("ine_get_study", {"idno": "999"})
    assert out["error"]["code"] == "upstream_error"


@respx.mock
async def test_list_ckan_datasets():
    payload = {
        "success": True,
        "result": {
            "count": 1,
            "results": [
                {
                    "id": "abc",
                    "name": "ine-precios",
                    "title": "Índice de Precios",
                    "notes": "desc",
                    "organization": {"title": "INE"},
                    "num_resources": 1,
                    "metadata_modified": "2026-01-01",
                    "resources": [
                        {
                            "id": "r1",
                            "name": "csv",
                            "format": "CSV",
                            "url": "http://x/r1.csv",
                        }
                    ],
                }
            ],
        },
    }
    route = respx.get(f"{CKAN_ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("ine_list_ckan_datasets", {"query": "precios"})

    assert route.called
    assert out["_meta"]["source"]["api"] == "catalogodatos.gub.uy"
    body = out["data"]
    assert body["count"] == 1
    ds = body["results"][0]
    assert ds["organization"] == "INE"
    assert ds["resources"][0]["format"] == "CSV"
    # Confirm the request was scoped to organization:ine.
    request = route.calls.last.request
    assert "organization%3Aine" in str(request.url) or "organization:ine" in str(request.url)


def test_ine_prompts_registered():
    by_name = {p.name: p for p in registry.prompts()}
    expected = {
        "ine_buscar_estudios",
        "ine_metadatos_estudio",
        "ine_datos_catalogo_nacional",
    }
    assert expected <= set(by_name)
    for name in expected:
        spec = by_name[name]
        assert spec.module == MODULE
        assert spec.description


def test_ine_resources_registered():
    by_uri = {r.uri: r for r in registry.resources()}
    expected = {"uru://ine/guia-fuentes", "uru://ine/idno-convencion"}
    assert expected <= set(by_uri)
    for uri in expected:
        spec = by_uri[uri]
        assert spec.module == MODULE
        assert spec.uri.startswith("uru://ine/")
        assert spec.mime_type == "text/markdown"


def test_ine_prompt_handlers_return_strings():
    by_name = {p.name: p for p in registry.prompts()}
    text = by_name["ine_buscar_estudios"].handler(tema="precios")
    assert isinstance(text, str)
    assert "ine_search_studies" in text


def test_ine_resource_handlers_return_strings():
    by_uri = {r.uri: r for r in registry.resources()}
    text = by_uri["uru://ine/guia-fuentes"].handler()
    assert isinstance(text, str)
    assert "ine_get_study" in text
