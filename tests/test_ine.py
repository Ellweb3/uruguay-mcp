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


@respx.mock
async def test_find_data_resources_keeps_only_datastore_active():
    payload = {
        "success": True,
        "result": {
            "count": 2,
            "results": [
                {
                    "name": "ine-precios",
                    "title": "Índice de Precios",
                    "resources": [
                        {
                            "id": "r-active",
                            "name": "serie",
                            "format": "CSV",
                            "datastore_active": True,
                            "url": "http://x/r-active.csv",
                        },
                        {
                            "id": "r-file",
                            "name": "pdf",
                            "format": "PDF",
                            "datastore_active": False,
                            "url": "http://x/r-file.pdf",
                        },
                    ],
                },
                {
                    "name": "ine-sin-datastore",
                    "title": "Solo descargas",
                    "resources": [
                        {
                            "id": "r-none",
                            "name": "xls",
                            "format": "XLSX",
                            "datastore_active": False,
                            "url": "http://x/r-none.xlsx",
                        }
                    ],
                },
            ],
        },
    }
    route = respx.get(f"{CKAN_ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("ine_find_data_resources", {"theme": "precios", "rows": 5})

    assert route.called
    assert out["_meta"]["source"]["api"] == "catalogodatos.gub.uy"
    body = out["data"]
    assert body["count"] == 2
    # Only the dataset with a datastore-active resource survives.
    assert body["datasets_with_data"] == 1
    assert body["active_resources"] == 1
    ds = body["results"][0]
    assert ds["dataset_name"] == "ine-precios"
    assert [r["id"] for r in ds["resources"]] == ["r-active"]
    assert ds["resources"][0]["datastore_active"] is True
    # Request was scoped to organization:ine.
    request = route.calls.last.request
    assert "organization%3Aine" in str(request.url) or "organization:ine" in str(request.url)


@respx.mock
async def test_datastore_query_slims_fields_and_records():
    payload = {
        "success": True,
        "result": {
            "resource_id": "r-active",
            "fields": [
                {"id": "_id", "type": "int"},
                {"id": "mes", "type": "text"},
                {"id": "valor", "type": "numeric"},
            ],
            "total": 3,
            "records": [
                {"_id": 1, "mes": "2026-01", "valor": "100.0"},
                {"_id": 2, "mes": "2026-02", "valor": "100.5"},
            ],
        },
    }
    route = respx.get(f"{CKAN_ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool(
        "ine_datastore_query", {"resource_id": "r-active", "limit": 2, "q": "2026"}
    )

    assert route.called
    assert out["_meta"]["source"]["api"] == "catalogodatos.gub.uy"
    body = out["data"]
    assert body["resource_id"] == "r-active"
    assert body["total"] == 3
    assert body["limit"] == 2
    assert {"id": "valor", "type": "numeric"} in body["fields"]
    assert body["records"][0]["mes"] == "2026-01"
    request = route.calls.last.request
    assert "resource_id=r-active" in str(request.url)
    assert "limit=2" in str(request.url)


@respx.mock
async def test_datastore_query_error_envelope_becomes_upstream_error():
    payload = {"success": False, "error": {"message": "Not found: resource_id"}}
    respx.get(f"{CKAN_ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(404, json=payload)
    )

    out = await meta.call_tool("ine_datastore_query", {"resource_id": "missing"})
    assert out["error"]["code"] == "upstream_error"


@respx.mock
async def test_datastore_fields_uses_limit_zero():
    payload = {
        "success": True,
        "result": {
            "resource_id": "r-active",
            "fields": [
                {"id": "_id", "type": "int"},
                {"id": "valor", "type": "numeric"},
            ],
            "total": 99,
            "records": [],
        },
    }
    route = respx.get(f"{CKAN_ACTION_URL}/datastore_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("ine_datastore_fields", {"resource_id": "r-active"})

    assert route.called
    body = out["data"]
    assert body["total"] == 99
    assert body["fields"] == [
        {"id": "_id", "type": "int"},
        {"id": "valor", "type": "numeric"},
    ]
    # Schema-only fetch must request zero rows.
    request = route.calls.last.request
    assert "limit=0" in str(request.url)


@respx.mock
async def test_dataset_resources_flags_queryable():
    payload = {
        "success": True,
        "result": {
            "id": "abc",
            "name": "ine-precios",
            "title": "Índice de Precios",
            "notes": "desc",
            "organization": {"title": "INE"},
            "num_resources": 2,
            "resources": [
                {
                    "id": "r-active",
                    "name": "serie",
                    "format": "CSV",
                    "datastore_active": True,
                    "url": "http://x/r-active.csv",
                },
                {
                    "id": "r-file",
                    "name": "pdf",
                    "format": "PDF",
                    "datastore_active": False,
                    "url": "http://x/r-file.pdf",
                },
            ],
        },
    }
    route = respx.get(f"{CKAN_ACTION_URL}/package_show").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("ine_dataset_resources", {"dataset_name": "ine-precios"})

    assert route.called
    assert out["_meta"]["source"]["api"] == "catalogodatos.gub.uy"
    body = out["data"]
    assert body["name"] == "ine-precios"
    assert body["organization"] == "INE"
    assert body["queryable_resources"] == ["r-active"]
    assert len(body["resources"]) == 2
    request = route.calls.last.request
    assert "id=ine-precios" in str(request.url)


@respx.mock
async def test_dataset_resources_not_found_becomes_error():
    payload = {"success": False, "error": {"message": "Not found"}}
    respx.get(f"{CKAN_ACTION_URL}/package_show").mock(
        return_value=httpx.Response(404, json=payload)
    )

    out = await meta.call_tool("ine_dataset_resources", {"dataset_name": "nope"})
    assert out["error"]["code"] == "upstream_error"


def test_ine_prompts_registered():
    by_name = {p.name: p for p in registry.prompts()}
    expected = {
        "ine_buscar_estudios",
        "ine_metadatos_estudio",
        "ine_datos_catalogo_nacional",
        "ine_consultar_serie_datos",
        "ine_explorar_recursos_dataset",
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
