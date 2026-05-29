"""Unit tests for the cross-source datastore module (HTTP mocked, offline)."""

from __future__ import annotations

import httpx
import pytest
import respx

import uruguay_mcp.modules.datastore  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.datastore import client
from uruguay_mcp.shared import cache, http

CSV_URL = "https://example.org/data/poblacion.csv"
CKAN_BASE = "https://catalogodatos.gub.uy"
CKAN_SEARCH = f"{CKAN_BASE}/api/3/action/datastore_search"

CSV_BODY = "depto,poblacion\nMontevideo,1319108\nCanelones,520187\n"


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    client.reset()
    yield
    cache.clear()
    client.reset()
    await http.aclose()


@respx.mock
async def test_load_csv_and_select():
    route = respx.get(CSV_URL).mock(return_value=httpx.Response(200, text=CSV_BODY))

    loaded = await meta.call_tool(
        "datastore_load_csv", {"url": CSV_URL, "table": "poblacion"}
    )
    assert route.called
    assert loaded["data"]["rows_loaded"] == 2
    assert loaded["data"]["table"] == "poblacion"
    assert loaded["data"]["columns"] == ["depto", "poblacion"]

    out = await meta.call_tool(
        "datastore_sql",
        {"query": "SELECT depto FROM poblacion ORDER BY depto"},
    )
    assert out["data"]["columns"] == ["depto"]
    assert out["data"]["rows"] == [["Canelones"], ["Montevideo"]]
    assert out["data"]["truncated"] is False


@respx.mock
async def test_sanitizes_table_name():
    respx.get(CSV_URL).mock(return_value=httpx.Response(200, text=CSV_BODY))
    loaded = await meta.call_tool(
        "datastore_load_csv", {"url": CSV_URL, "table": "123 mi tabla!"}
    )
    # Leading digit prefixed, spaces/punctuation -> underscores.
    assert loaded["data"]["table"] == "t_123_mi_tabla"


@respx.mock
async def test_list_tables_reports_counts_and_columns():
    respx.get(CSV_URL).mock(return_value=httpx.Response(200, text=CSV_BODY))
    await meta.call_tool("datastore_load_csv", {"url": CSV_URL, "table": "poblacion"})

    out = await meta.call_tool("datastore_list_tables", {})
    assert out["data"]["count"] == 1
    tbl = out["data"]["tables"][0]
    assert tbl["table"] == "poblacion"
    assert tbl["row_count"] == 2
    assert tbl["columns"] == ["depto", "poblacion"]


async def test_rejects_non_select():
    out = await meta.call_tool(
        "datastore_sql", {"query": "DROP TABLE poblacion"}
    )
    assert out["error"]["code"] == "validation_error"


async def test_rejects_multiple_statements():
    out = await meta.call_tool(
        "datastore_sql",
        {"query": "SELECT 1; DELETE FROM poblacion"},
    )
    assert out["error"]["code"] == "validation_error"


async def test_rejects_pragma():
    out = await meta.call_tool("datastore_sql", {"query": "PRAGMA table_info(x)"})
    assert out["error"]["code"] == "validation_error"


@respx.mock
async def test_load_ckan_resource_and_join():
    page = {
        "success": True,
        "result": {
            "fields": [{"id": "_id"}, {"id": "depto"}, {"id": "presupuesto"}],
            "records": [
                {"_id": 1, "depto": "Montevideo", "presupuesto": "1000"},
                {"_id": 2, "depto": "Canelones", "presupuesto": "500"},
            ],
        },
    }
    empty = {"success": True, "result": {"fields": [], "records": []}}
    respx.get(CSV_URL).mock(return_value=httpx.Response(200, text=CSV_BODY))
    respx.get(CKAN_SEARCH).mock(
        side_effect=[
            httpx.Response(200, json=page),
            httpx.Response(200, json=empty),
        ]
    )

    await meta.call_tool("datastore_load_csv", {"url": CSV_URL, "table": "censo"})
    loaded = await meta.call_tool(
        "datastore_load_ckan_resource",
        {"resource_id": "abc-123", "table": "gasto", "max_rows": 5000},
    )
    assert loaded["data"]["rows_loaded"] == 2
    assert loaded["data"]["columns"] == ["depto", "presupuesto"]

    out = await meta.call_tool(
        "datastore_sql",
        {
            "query": (
                "SELECT c.depto, c.poblacion, g.presupuesto "
                "FROM censo c JOIN gasto g ON c.depto = g.depto "
                "ORDER BY c.depto"
            )
        },
    )
    assert out["data"]["columns"] == ["depto", "poblacion", "presupuesto"]
    assert out["data"]["rows"] == [
        ["Canelones", "520187", "500"],
        ["Montevideo", "1319108", "1000"],
    ]
