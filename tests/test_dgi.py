"""Unit tests for the DGI (Dirección General Impositiva) module, HTTP mocked."""

from __future__ import annotations

import io
import zipfile

import httpx
import pytest
import respx

import uruguay_mcp.modules.dgi  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.dgi.constants import (
    BASE_URL,
    BOLETIN_PATH,
    DATOS_PATH,
    MODULE,
)
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry

_FILES = "https://www.gub.uy/direccion-general-impositiva/sites/direccion-general-impositiva/files"


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


def _build_ods(content_xml: str) -> bytes:
    """Build a minimal real ODS: ZIP with `mimetype` + `content.xml`."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # The mimetype entry must be the first, stored uncompressed per spec;
        # the parser doesn't require it, but we keep it realistic.
        zf.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet")
        zf.writestr("content.xml", content_xml)
    return buf.getvalue()


# A document with 2 sheets. Sheet 0 exercises:
#  - a <text:p> cell,
#  - table:number-columns-repeated (expansion),
#  - trailing-empty trimming,
#  - a fully-empty spacer row (number-rows-repeated) that must be skipped.
_CONTENT_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<office:document-content '
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
    "<office:body><office:spreadsheet>"
    '<table:table table:name="Hoja1">'
    # Header row: "Fecha" then "Valor" repeated x2 (→ Valor, Valor) then trailing empties.
    "<table:table-row>"
    "<table:table-cell><text:p>Fecha</text:p></table:table-cell>"
    '<table:table-cell table:number-columns-repeated="2"><text:p>Valor</text:p></table:table-cell>'
    '<table:table-cell table:number-columns-repeated="5"/>'
    "</table:table-row>"
    # A fully-empty spacer row repeated 700 times → must be skipped entirely.
    '<table:table-row table:number-rows-repeated="700">'
    '<table:table-cell table:number-columns-repeated="9"/>'
    "</table:table-row>"
    # Data row with a numeric cell carrying office:value and a text cell.
    "<table:table-row>"
    "<table:table-cell><text:p>2025-01-02</text:p></table:table-cell>"
    '<table:table-cell office:value="5.7843"><text:p>5,7843</text:p></table:table-cell>'
    "</table:table-row>"
    "</table:table>"
    '<table:table table:name="Hoja2">'
    "<table:table-row>"
    "<table:table-cell><text:p>OtraHoja</text:p></table:table-cell>"
    "</table:table-row>"
    "</table:table>"
    "</office:spreadsheet></office:body></office:document-content>"
)


def _datos_page(anchors: list[tuple[str, str]]) -> str:
    """Build a listing HTML page from (href, visible_text) anchors."""
    cards = "".join(
        f'<div><a href="{href}" download>{text}</a></div>' for href, text in anchors
    )
    return f"<html><body>{cards}</body></html>"


# --- ODS parsing ----------------------------------------------------------


@respx.mock
async def test_tabla_parses_ods_with_repeats_and_spacers():
    ods = _build_ods(_CONTENT_XML)
    url = f"{_FILES}/2026-02/unidad-indexada.ods"
    respx.get(url).mock(return_value=httpx.Response(200, content=ods))

    out = await meta.call_tool("dgi_tabla", {"url": url})
    body = out["data"]

    assert body["formato"] == "ods"
    assert body["n_hojas"] == 2
    # Header expanded the repeat (Valor x2) and trimmed trailing empties; the
    # 700x empty spacer row was skipped; data row present.
    assert body["filas"] == [
        ["Fecha", "Valor", "Valor"],
        ["2025-01-02", "5,7843"],
    ]
    assert body["n_filas"] == 2


@respx.mock
async def test_tabla_reads_second_sheet():
    ods = _build_ods(_CONTENT_XML)
    url = f"{_FILES}/2026-02/unidad-indexada.ods"
    respx.get(url).mock(return_value=httpx.Response(200, content=ods))

    out = await meta.call_tool("dgi_tabla", {"url": url, "hoja": 1})
    body = out["data"]
    assert body["hoja"] == 1
    assert body["filas"] == [["OtraHoja"]]


async def test_tabla_rejects_non_gubuy_url():
    out = await meta.call_tool(
        "dgi_tabla", {"url": "https://example.com/data/file.ods"}
    )
    assert out["error"]["code"] == "upstream_error"
    assert "no permitida" in out["error"]["message"]


# --- Listing --------------------------------------------------------------


@respx.mock
async def test_listar_datos_across_pages_with_dedupe_and_tema_filter():
    page0 = _datos_page(
        [
            (f"{_FILES}/2026-01/ui.ods", "Unidad indexada 2023 - 2025"),
            (f"{_FILES}/2025-12/ipc.ods", "Índice de Precios al Consumo 2011-2025"),
        ]
    )
    # Page 1 repeats ui.ods (dedup) and adds a new csv file.
    page1 = _datos_page(
        [
            (f"{_FILES}/2026-01/ui.ods", "Unidad indexada 2023 - 2025"),
            (f"{_FILES}/2026-02/cotizaciones.csv", "Cotizaciones interbancarias"),
        ]
    )
    page2 = "<html><body>sin archivos</body></html>"

    # Register the specific (page=N) routes first so they win over the base one.
    respx.get(f"{BASE_URL}{DATOS_PATH}", params={"page": "2"}).mock(
        return_value=httpx.Response(200, text=page2)
    )
    respx.get(f"{BASE_URL}{DATOS_PATH}", params={"page": "1"}).mock(
        return_value=httpx.Response(200, text=page1)
    )
    respx.get(f"{BASE_URL}{DATOS_PATH}").mock(
        return_value=httpx.Response(200, text=page0)
    )

    out = await meta.call_tool("dgi_listar_datos", {})
    body = out["data"]
    # 2 + 1 new (ui deduped) = 3
    assert body["total"] == 3
    urls = {r["url"] for r in body["results"]}
    assert f"{_FILES}/2026-01/ui.ods" in urls
    assert f"{_FILES}/2026-02/cotizaciones.csv" in urls
    ui = next(r for r in body["results"] if r["url"].endswith("ui.ods"))
    assert ui["titulo"] == "Unidad indexada 2023 - 2025"
    assert ui["formato"] == "ods"
    assert ui["periodo"] == "2026-01"

    # tema filter (accent/case-insensitive substring on titulo).
    out2 = await meta.call_tool("dgi_listar_datos", {"tema": "indice de precios"})
    body2 = out2["data"]
    assert body2["total"] == 1
    assert body2["results"][0]["url"].endswith("ipc.ods")

    # formato filter.
    out3 = await meta.call_tool("dgi_listar_datos", {"formato": "csv"})
    assert out3["data"]["total"] == 1
    assert out3["data"]["results"][0]["formato"] == "csv"


@respx.mock
async def test_buscar_valor_picks_most_recent_periodo():
    page0 = _datos_page(
        [
            (f"{_FILES}/2024-03/recargos-mora.ods", "Tasas de recargos Art. 94"),
            (f"{_FILES}/2026-02/recargos-mora.ods", "Tasas de recargos Art. 94"),
        ]
    )
    page1 = "<html><body></body></html>"
    respx.get(f"{BASE_URL}{DATOS_PATH}", params={"page": "1"}).mock(
        return_value=httpx.Response(200, text=page1)
    )
    respx.get(f"{BASE_URL}{DATOS_PATH}").mock(
        return_value=httpx.Response(200, text=page0)
    )
    chosen = f"{_FILES}/2026-02/recargos-mora.ods"
    respx.get(chosen).mock(
        return_value=httpx.Response(200, content=_build_ods(_CONTENT_XML))
    )

    out = await meta.call_tool("dgi_buscar_valor", {"query": "recargos"})
    body = out["data"]
    assert body["encontrado"] is True
    assert body["periodo"] == "2026-02"
    assert body["url"] == chosen
    assert body["filas"][0] == ["Fecha", "Valor", "Valor"]


@respx.mock
async def test_buscar_valor_not_found_returns_encontrado_false():
    respx.get(f"{BASE_URL}{DATOS_PATH}", params={"page": "1"}).mock(
        return_value=httpx.Response(200, text="<html></html>")
    )
    respx.get(f"{BASE_URL}{DATOS_PATH}").mock(
        return_value=httpx.Response(
            200, text=_datos_page([(f"{_FILES}/2026-01/ui.ods", "Unidad indexada")])
        )
    )

    out = await meta.call_tool("dgi_buscar_valor", {"query": "no-existe-esto"})
    assert out["data"] == {"encontrado": False, "query": "no-existe-esto"}


# --- Boletines ------------------------------------------------------------


@respx.mock
async def test_boletines_extracts_pdfs_with_anio():
    page = (
        "<html><body>"
        f'<a href="{_FILES}/2025-04/Boletin%20Estadistico%202024.pdf">'
        "Boletín Estadístico 2024</a>"
        f'<a href="{_FILES}/2024-03/Boletin%20Estadistico%202023.pdf">'
        "Boletín Estadístico 2023</a>"
        f'<a href="{_FILES}/2024-03/algo.ods">no es pdf</a>'
        "</body></html>"
    )
    respx.get(f"{BASE_URL}{BOLETIN_PATH}").mock(
        return_value=httpx.Response(200, text=page)
    )

    out = await meta.call_tool("dgi_boletines", {})
    body = out["data"]
    assert body["total"] == 2
    anios = {r["anio"] for r in body["results"]}
    assert anios == {2024, 2023}
    assert all(r["categoria"] == "boletin" for r in body["results"])


# --- Cache ----------------------------------------------------------------


@respx.mock
async def test_datos_cache():
    respx.get(f"{BASE_URL}{DATOS_PATH}", params={"page": "1"}).mock(
        return_value=httpx.Response(200, text="<html></html>")
    )
    route = respx.get(f"{BASE_URL}{DATOS_PATH}").mock(
        return_value=httpx.Response(
            200, text=_datos_page([(f"{_FILES}/2026-01/ui.ods", "Unidad indexada")])
        )
    )

    first = await meta.call_tool("dgi_listar_datos", {})
    second = await meta.call_tool("dgi_listar_datos", {})
    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


# --- Registration ---------------------------------------------------------


def test_dgi_prompts_registered():
    by_name = {p.name: p for p in registry.prompts()}
    expected = {"dgi_valor_referencia", "dgi_consultar_tabla"}
    assert expected <= set(by_name)
    for name in expected:
        spec = by_name[name]
        assert spec.module == MODULE
        assert spec.description


def test_dgi_resources_registered():
    by_uri = {r.uri: r for r in registry.resources()}
    expected = {"uru://dgi/catalogo-valores", "uru://dgi/fuentes"}
    assert expected <= set(by_uri)
    for uri in expected:
        spec = by_uri[uri]
        assert spec.module == MODULE
        assert spec.uri.startswith("uru://dgi/")
        assert spec.mime_type == "text/markdown"


def test_dgi_prompt_handlers_return_strings():
    by_name = {p.name: p for p in registry.prompts()}
    text = by_name["dgi_valor_referencia"].handler(tema="IPC")
    assert isinstance(text, str)
    assert "dgi_buscar_valor" in text
    assert "dgi_listar_datos" in text
    assert "dgi_tabla" in text


def test_dgi_resource_handlers_return_strings():
    by_uri = {r.uri: r for r in registry.resources()}
    text = by_uri["uru://dgi/fuentes"].handler()
    assert isinstance(text, str)
    assert "dgi_listar_datos" in text
    assert "dgi_tabla" in text


# --- Live integration -----------------------------------------------------


@pytest.mark.integration
async def test_listar_datos_live_finds_ods():
    out = await meta.call_tool("dgi_listar_datos", {})
    body = out["data"]
    assert body["total"] > 0
    assert any(r["formato"] == "ods" for r in body["results"])
