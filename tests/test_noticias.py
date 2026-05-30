"""Unit tests for the noticias (gub.uy) module, with the HTTP layer mocked."""

from __future__ import annotations

import httpx
import pytest
import respx

import uruguay_mcp.modules.noticias  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.noticias.constants import BASE_URL
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry

# Presidencia layout: Box-title / Box-subtitle, date "29 de Mayo, 2026".
PRESIDENCIA_HTML = """<html><body>
<article about="/presidencia/comunicacion/noticias/primera-noticia">
  <div class="Box-subtitle"><div>Comunicado</div></div>
  <h3 class="Box-title"><a href="/presidencia/comunicacion/noticias/primera-noticia">
    Presidente anuncia plan &quot;ABC&quot;</a></h3>
  <div class="Box-info">29 de Mayo, 2026</div>
  <div>Este es un resumen suficientemente largo de la primera noticia oficial.</div>
</article>
<article about="/presidencia/comunicacion/noticias/segunda-noticia">
  <div class="Box-subtitle"><div>Salud</div></div>
  <h3 class="Box-title"><a href="/presidencia/comunicacion/noticias/segunda-noticia">
    Segunda noticia con acentuaci&oacute;n</a></h3>
  <div class="Box-info">28 de Setiembre, 2026</div>
  <div>Resumen de la segunda noticia, tambien con longitud suficiente para pasar.</div>
</article>
</body></html>"""

# Ministry layout: Media-title / Media-subtitle, date "29/05/2026".
MINISTRY_HTML = """<html><body>
<li class="Media">
<article about="/ministerio-salud-publica/comunicacion/noticias/aviso-sanitario">
  <span class="Media-subtitle">Aviso</span>
  <h3 class="Media-title"><a rel="bookmark"
    href="/ministerio-salud-publica/comunicacion/noticias/aviso-sanitario">
    Aviso sanitario importante</a></h3>
  <span class="Box-info">29/05/2026</span>
  <div><p>Texto del aviso sanitario con la longitud necesaria para el resumen.</p></div>
</article>
</li>
</body></html>"""

SEARCH_HTML = """<html><body>
<ul class="Results">
<li class="Results-item">
  <h3 class="Results-title"><a href="https://www.gub.uy/presidencia/comunicacion/noticias/x"
    target="_blank">Noticia encontrada</a></h3>
  <p class="Results-url">www.gub.uy/presidencia/comunicacion/noticias/x</p>
  <p class="Results-summary">31 may 2026 ... fragmento del buscador.</p>
</li>
<li class="Results-item">
  <h3 class="Results-title"><a href="https://www.montevideo.gub.uy/algo-no-noticia"
    target="_blank">Resultado ajeno</a></h3>
  <p class="Results-url">www.montevideo.gub.uy/algo-no-noticia</p>
  <p class="Results-summary">No es una noticia y debe filtrarse.</p>
</li>
</ul>
</body></html>"""

LISTING_URL = f"{BASE_URL}/presidencia/comunicacion/noticias"
MIN_LISTING_URL = f"{BASE_URL}/ministerio-salud-publica/comunicacion/noticias"
SEARCH_URL = f"{BASE_URL}/buscar"


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


@respx.mock
async def test_recientes_parses_presidencia_layout():
    route = respx.get(LISTING_URL).mock(
        return_value=httpx.Response(200, text=PRESIDENCIA_HTML)
    )

    out = await meta.call_tool("noticias_recientes", {"limit": 5})

    assert route.called
    assert out["_meta"]["source"]["api"] == "gub.uy"
    assert out["_meta"]["cached"] is False
    body = out["data"]
    assert body["count"] == 2
    assert body["subsite"] == "presidencia"
    first = body["results"][0]
    # HTML entities unescaped.
    assert first["titulo"] == 'Presidente anuncia plan "ABC"'
    assert first["categoria"] == "Comunicado"
    # Spanish-month date normalized to ISO.
    assert first["fecha"] == "2026-05-29"
    assert first["url"] == f"{BASE_URL}/presidencia/comunicacion/noticias/primera-noticia"
    assert "primera noticia" in first["resumen"]
    # "Setiembre" handled.
    assert body["results"][1]["fecha"] == "2026-09-28"
    assert "no publica RSS" in body["nota"]


@respx.mock
async def test_recientes_parses_ministry_layout_numeric_date():
    respx.get(MIN_LISTING_URL).mock(return_value=httpx.Response(200, text=MINISTRY_HTML))

    out = await meta.call_tool(
        "noticias_recientes", {"subsite": "ministerio-salud-publica", "limit": 5}
    )

    body = out["data"]
    assert body["count"] == 1
    card = body["results"][0]
    assert card["titulo"] == "Aviso sanitario importante"
    assert card["categoria"] == "Aviso"
    assert card["fecha"] == "2026-05-29"  # DD/MM/YYYY normalized
    assert card["url"].endswith("/comunicacion/noticias/aviso-sanitario")


@respx.mock
async def test_recientes_paginates_to_fill_limit():
    # Page 0 returns 10 full cards (triggers a second fetch); page 1 returns 2.
    page0 = "".join(
        f'<article about="/presidencia/comunicacion/noticias/n{i}">'
        f'<div class="Box-subtitle"><div>Cat</div></div>'
        f'<h3 class="Box-title"><a href="/presidencia/comunicacion/noticias/n{i}">'
        f"Titulo {i}</a></h3>"
        f'<div class="Box-info">29 de Mayo, 2026</div>'
        f"<div>Resumen numero {i} con longitud suficiente para el parser ok.</div>"
        f"</article>"
        for i in range(10)
    )
    # Register the more specific (page=1) route first so it wins for that request.
    route1 = respx.get(LISTING_URL, params={"page": "1"}).mock(
        return_value=httpx.Response(200, text=PRESIDENCIA_HTML)
    )
    route0 = respx.get(LISTING_URL).mock(
        return_value=httpx.Response(200, text=f"<body>{page0}</body>")
    )

    out = await meta.call_tool("noticias_recientes", {"limit": 12})

    assert route0.called and route1.called
    assert out["data"]["count"] == 12


@respx.mock
async def test_recientes_is_cached_on_second_call():
    route = respx.get(LISTING_URL).mock(
        return_value=httpx.Response(200, text=PRESIDENCIA_HTML)
    )

    first = await meta.call_tool("noticias_recientes", {"limit": 2})
    second = await meta.call_tool("noticias_recientes", {"limit": 2})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


@respx.mock
async def test_recientes_upstream_error():
    respx.get(LISTING_URL).mock(return_value=httpx.Response(503))

    out = await meta.call_tool("noticias_recientes", {"limit": 2})
    assert out["error"]["code"] == "upstream_error"


@respx.mock
async def test_buscar_filters_to_news_urls():
    route = respx.get(SEARCH_URL).mock(
        return_value=httpx.Response(200, text=SEARCH_HTML)
    )

    out = await meta.call_tool("noticias_buscar", {"query": "salud"})

    assert route.called
    # The form field must be search_api_fulltext (not 'keys').
    assert route.calls.last.request.url.params["search_api_fulltext"] == "salud"
    body = out["data"]
    assert body["status"] == "partial"
    assert body["count"] == 1  # montevideo result filtered out
    assert body["results"][0]["titulo"] == "Noticia encontrada"
    assert "/comunicacion/noticias/" in body["results"][0]["url"]


@respx.mock
async def test_buscar_subsite_variant_url():
    route = respx.get(f"{BASE_URL}/presidencia/buscar").mock(
        return_value=httpx.Response(200, text=SEARCH_HTML)
    )

    out = await meta.call_tool(
        "noticias_buscar", {"query": "plan", "subsite": "presidencia"}
    )

    assert route.called
    assert out["_meta"]["source"]["url"].startswith(f"{BASE_URL}/presidencia/buscar")


def test_module_prompts_registered():
    names = {p.name for p in registry.prompts() if p.module == "noticias"}
    assert {"noticias_ultimas", "noticias_buscar_tema"} <= names


def test_module_resources_registered():
    uris = {r.uri for r in registry.resources() if r.module == "noticias"}
    assert {
        "uru://noticias/guia-de-uso",
        "uru://noticias/subsitios",
    } <= uris


def test_prompt_text_references_real_tools():
    by_name = {p.name: p for p in registry.prompts()}
    assert "noticias_recientes" in by_name["noticias_ultimas"].handler()
    assert "noticias_buscar" in by_name["noticias_buscar_tema"].handler(tema="salud")


def test_noticias_new_prompt_registered():
    names = {p.name for p in registry.prompts() if p.module == "noticias"}
    assert "noticias_monitorear_tema" in names


def test_noticias_monitorear_tema_handler_references_tools():
    by_name = {p.name: p for p in registry.prompts()}
    text = by_name["noticias_monitorear_tema"].handler(tema="salud")
    assert isinstance(text, str)
    assert "noticias_buscar" in text
    assert "noticias_recientes" in text
