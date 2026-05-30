"""Unit tests for the ACCE module, with the HTTP layer mocked."""

from __future__ import annotations

import httpx
import pytest
import respx

import uruguay_mcp.modules.acce  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.acce.constants import (
    CKAN_ACTION_URL,
    RECORD_URL,
    RELEASE_URL,
    RSS_URL,
)
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry

RSS_BODY = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>OCDS</title>
    <item>
      <title>id_compra:1343954,release_id:llamado-1343954</title>
      <pubDate>Fri, 29 May 2026 19:56:02</pubDate>
      <link>http://www.comprasestatales.gub.uy/ocds/release/llamado-1343954</link>
      <guid>llamado-1343954</guid>
      <category>tender</category>
    </item>
    <item>
      <title>id_compra:1342977,release_id:adjudicacion-1342977</title>
      <pubDate>Fri, 29 May 2026 18:10:00</pubDate>
      <link>http://www.comprasestatales.gub.uy/ocds/release/adjudicacion-1342977</link>
      <guid>adjudicacion-1342977</guid>
      <category>award</category>
    </item>
  </channel>
</rss>
"""


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


@respx.mock
async def test_recientes_parses_rss():
    route = respx.get(RSS_URL).mock(
        return_value=httpx.Response(200, text=RSS_BODY)
    )

    out = await meta.call_tool("acce_recientes", {"limit": 10})

    assert route.called
    assert out["_meta"]["source"]["api"] == "comprasestatales.gub.uy/ocds"
    assert out["_meta"]["cached"] is False
    body = out["data"]
    assert body["count"] == 2
    first = body["results"][0]
    assert first["id_compra"] == "1343954"
    assert first["release_id"] == "llamado-1343954"
    assert first["tag"] == "tender"


@respx.mock
async def test_recientes_filters_by_tag():
    respx.get(RSS_URL).mock(return_value=httpx.Response(200, text=RSS_BODY))

    out = await meta.call_tool("acce_recientes", {"tag": "award"})

    body = out["data"]
    assert body["count"] == 1
    assert body["results"][0]["release_id"] == "adjudicacion-1342977"


@respx.mock
async def test_recientes_monthly_variant_url():
    route = respx.get(f"{RSS_URL}/2026/04").mock(
        return_value=httpx.Response(200, text=RSS_BODY)
    )

    out = await meta.call_tool("acce_recientes", {"year": 2026, "month": 4})

    assert route.called
    assert out["_meta"]["source"]["url"].endswith("/rss/2026/04")


@respx.mock
async def test_recientes_is_cached_on_second_call():
    route = respx.get(RSS_URL).mock(return_value=httpx.Response(200, text=RSS_BODY))

    first = await meta.call_tool("acce_recientes", {})
    second = await meta.call_tool("acce_recientes", {})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


@respx.mock
async def test_get_compra_enumerates_events():
    payload = {
        "publishedDate": "2026-05-29T00:00:00",
        "records": [
            {
                "ocid": "ocds-yfs5dr-1343954",
                "releases": [
                    {
                        "url": f"{RELEASE_URL}/llamado-1343954",
                        "date": "2026-05-29",
                        "tag": ["tender"],
                    },
                    {
                        "url": f"{RELEASE_URL}/adjudicacion-1343954",
                        "date": "2026-05-30",
                        "tag": ["award"],
                    },
                ],
            }
        ],
    }
    respx.get(f"{RECORD_URL}/1343954").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("acce_get_compra", {"idcompra": "1343954"})

    body = out["data"]
    assert body["ocid"] == "ocds-yfs5dr-1343954"
    assert len(body["events"]) == 2
    assert body["events"][0]["release_id"] == "llamado-1343954"
    assert body["events"][1]["tag"] == ["award"]


@respx.mock
async def test_get_compra_404_is_not_found():
    respx.get(f"{RECORD_URL}/999").mock(
        return_value=httpx.Response(404, json={"message": " no se encuentra en el sistema"})
    )

    out = await meta.call_tool("acce_get_compra", {"idcompra": "999"})
    assert out["error"]["code"] == "not_found"


@respx.mock
async def test_get_release_tender_slimmed():
    payload = {
        "releases": [
            {
                "ocid": "ocds-yfs5dr-1343954",
                "id": "llamado-1343954",
                "date": "2026-05-29",
                "tag": ["tender"],
                "initiationType": "tender",
                "buyer": {"name": "Organismo X"},
                "parties": [
                    {"id": "p1", "name": "Organismo X", "roles": ["procuringEntity"]}
                ],
                "tender": {
                    "id": "t1",
                    "title": "Compra de insumos",
                    "status": "active",
                    "procurementMethodDetails": "Licitación Abreviada",
                    "procuringEntity": {"name": "Organismo X"},
                    "value": None,
                    "tenderPeriod": {"startDate": "2026-05-29", "endDate": "2026-06-10"},
                    "items": [
                        {"id": "i1", "description": "Papel", "quantity": 10}
                    ],
                },
            }
        ]
    }
    respx.get(f"{RELEASE_URL}/llamado-1343954").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("acce_get_release", {"param": "llamado-1343954"})

    body = out["data"]
    assert body["tender"]["title"] == "Compra de insumos"
    assert body["tender"]["value"] is None
    assert body["tender"]["items"]["count"] == 1
    assert "awards" not in body


@respx.mock
async def test_get_release_award_without_value():
    payload = {
        "releases": [
            {
                "ocid": "ocds-yfs5dr-1342977",
                "id": "adjudicacion-1342977",
                "tag": ["award"],
                "awards": [
                    {
                        "id": "a1",
                        "status": "active",
                        "suppliers": [{"id": "s1", "name": "Proveedor SA"}],
                        "items": [],
                    }
                ],
            }
        ]
    }
    respx.get(f"{RELEASE_URL}/adjudicacion-1342977").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("acce_get_release", {"param": "adjudicacion-1342977"})

    body = out["data"]
    assert body["awards"][0]["suppliers"][0]["name"] == "Proveedor SA"
    assert body["awards"][0]["value"] is None


@respx.mock
async def test_buscar_forces_org_filter():
    payload = {
        "success": True,
        "result": {
            "count": 1,
            "results": [
                {
                    "id": "abc",
                    "name": "rupe-2026",
                    "title": "RUPE 2026",
                    "organization": {"title": "ACCE"},
                    "tags": [{"name": "proveedores"}],
                    "num_resources": 1,
                    "resources": [
                        {
                            "id": "r1",
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

    out = await meta.call_tool("acce_buscar", {"query": "rupe", "rows": 5})

    assert route.called
    assert route.calls.last.request.url.params["fq"] == "organization:acce"
    body = out["data"]
    assert body["count"] == 1
    assert body["results"][0]["organization"] == "ACCE"


@respx.mock
async def test_buscar_ckan_failure_is_error():
    payload = {"success": False, "error": {"message": "boom"}}
    respx.get(f"{CKAN_ACTION_URL}/package_search").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("acce_buscar", {"query": "x"})
    assert out["error"]["code"] == "upstream_error"


def test_module_prompts_registered():
    names = {p.name for p in registry.prompts() if p.module == "acce"}
    assert {
        "acce_compras_recientes",
        "acce_analizar_compra",
        "acce_buscar_datasets",
    } <= names


def test_module_resources_registered():
    uris = {r.uri for r in registry.resources() if r.module == "acce"}
    assert {
        "uru://acce/guia-de-uso",
        "uru://acce/glosario-ocds",
    } <= uris


def test_prompt_text_references_real_tools():
    by_name = {p.name: p for p in registry.prompts()}
    text = by_name["acce_analizar_compra"].handler(idcompra="1343954")
    assert "acce_get_compra" in text
    assert "acce_get_release" in text
