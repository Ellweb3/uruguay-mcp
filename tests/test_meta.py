"""Tests for the meta-discovery layer over the registered tools."""

from __future__ import annotations

import pytest

import uruguay_mcp.modules.catalogodatos  # noqa: F401  (registers tools)
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.meta.search import search


def test_modules_loaded():
    """The catalog module registers its tools and metadata."""
    info = pytest.importorskip("uruguay_mcp.shared.registry").registry.module_info("catalogodatos")
    assert info is not None
    assert "CKAN" in info.description or "Datos Abiertos" in info.title


def test_search_ranks_relevant_tool_first():
    # Scope to catalogodatos: the full suite loads other modules whose tools
    # share the same global registry, so an unscoped search is non-deterministic.
    results = search("buscar datasets de salud", limit=5, module="catalogodatos")
    assert results, "expected at least one match"
    top = results[0][0]
    assert top.name == "catalogo_search_datasets"


def test_search_respects_module_filter():
    results = search("organizaciones", module="catalogodatos")
    assert all(spec.module == "catalogodatos" for spec, _ in results)


async def test_discover_tools_returns_schema():
    out = await meta.discover_tools("consultar registros tabulares de un recurso")
    assert out["matches"]
    assert "arguments" in out["matches"][0]


async def test_list_modules():
    out = await meta.list_modules()
    names = {m["name"] for m in out["modules"]}
    assert "catalogodatos" in names
    assert out["total_tools"] >= 5


async def test_call_unknown_tool_returns_error_envelope():
    out = await meta.call_tool("does_not_exist", {})
    assert out["error"]["code"] == "not_found"


async def test_call_tool_validates_arguments():
    # get_dataset requires `id`; omitting it should yield a validation error.
    out = await meta.call_tool("catalogo_get_dataset", {})
    assert out["error"]["code"] == "validation_error"
