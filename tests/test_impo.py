"""Unit tests for the IMPO module, with the HTTP layer mocked."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

import uruguay_mcp.modules.impo  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.impo.constants import BASE_URL
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


def _latin1_response(payload: dict) -> httpx.Response:
    """Build a response encoded as IMPO does: latin-1 + charset header."""
    body = json.dumps(payload, ensure_ascii=False).encode("iso-8859-1")
    return httpx.Response(
        200, content=body, headers={"Content-Type": "application/json; charset=ISO-8859-1"}
    )


_LEY_PAYLOAD = {
    "tipoNorma": "Ley",
    "nroNorma": "18331",
    "anioNorma": "2008",
    "nombreNorma": "Protección de Datos Personales",
    "leyenda": "Documento Actualizado",
    "fechaPromulgacion": "2008-08-11",
    "fechaPublicacion": "2008-08-18",
    "urlVerImagen": "/diariooficial/2008/08/18/5",
    "vistos": "Vistos...",
    "firmantes": "VÁZQUEZ",
    "articulos": [
        {
            "nroArticulo": "1",
            "secArticulo": "1",
            "tituloArticulo": "<b>Derecho humano</b>",
            "textoArticulo": "El derecho a la protección de datos personales...",
            "urlArticulo": "/bases/leyes/18331-2008/1",
            "notasArticulo": 'Ver <a href="/x">ficha</a>',
        },
        {"nroArticulo": "2", "textoArticulo": "Ámbito de aplicación."},
    ],
}


@respx.mock
async def test_get_norma_decodes_latin1_and_slims():
    url = f"{BASE_URL}/bases/leyes/18331-2008"
    route = respx.get(url).mock(return_value=_latin1_response(_LEY_PAYLOAD))

    out = await meta.call_tool(
        "impo_get_norma", {"tipo": "ley", "numero": "18331", "anio": 2008}
    )

    assert route.called
    assert dict(route.calls.last.request.url.params)["json"] == "true"
    assert out["_meta"]["source"]["api"] == "impo.com.uy"
    assert out["_meta"]["cached"] is False
    data = out["data"]
    # Latin-1 accents survive the round-trip (not mojibake).
    assert data["nombreNorma"] == "Protección de Datos Personales"
    assert data["totalArticulos"] == 2
    art = data["articulos"][0]
    # Embedded HTML stripped; relative urlArticulo made absolute.
    assert art["tituloArticulo"] == "Derecho humano"
    assert art["notasArticulo"] == "Ver ficha"
    assert art["urlArticulo"] == f"{BASE_URL}/bases/leyes/18331-2008/1"
    assert data["urlVerImagen"] == f"{BASE_URL}/diariooficial/2008/08/18/5"


@respx.mock
async def test_get_norma_max_articulos_caps_list():
    url = f"{BASE_URL}/bases/leyes/18331-2008"
    respx.get(url).mock(return_value=_latin1_response(_LEY_PAYLOAD))

    out = await meta.call_tool(
        "impo_get_norma",
        {"tipo": "ley", "numero": "18331", "anio": 2008, "max_articulos": 1},
    )

    assert out["data"]["totalArticulos"] == 2  # total is the real count
    assert len(out["data"]["articulos"]) == 1  # but list is capped


@respx.mock
async def test_get_norma_original_uses_originales_slug():
    url = f"{BASE_URL}/bases/decretos-originales/500-1991"
    route = respx.get(url).mock(
        return_value=_latin1_response({"tipoNorma": "Decreto", "leyenda": "Documento original"})
    )

    out = await meta.call_tool(
        "impo_get_norma",
        {"tipo": "decreto", "numero": "500", "anio": 1991, "version": "original"},
    )

    assert route.called
    assert out["data"]["leyenda"] == "Documento original"


@respx.mock
async def test_get_norma_constitucion_uses_year_range():
    url = f"{BASE_URL}/bases/constitucion/1967-1967"
    route = respx.get(url).mock(
        return_value=_latin1_response(
            {"tipoNorma": "Constitución", "nombreNorma": "Constitución"}
        )
    )

    out = await meta.call_tool("impo_get_norma", {"tipo": "constitucion", "anio": 1967})

    assert route.called
    assert out["data"]["nombreNorma"] == "Constitución"


async def test_get_norma_missing_numero_is_validation_error():
    out = await meta.call_tool("impo_get_norma", {"tipo": "ley", "anio": 2008})
    assert out["error"]["code"] == "validation_error"


async def test_get_norma_original_constitucion_rejected():
    out = await meta.call_tool(
        "impo_get_norma", {"tipo": "constitucion", "anio": 1967, "version": "original"}
    )
    assert out["error"]["code"] == "validation_error"


@respx.mock
async def test_get_norma_html_response_becomes_upstream_error():
    url = f"{BASE_URL}/bases/leyes/99999-1900"
    respx.get(url).mock(
        return_value=httpx.Response(200, content=b"<html>not found</html>")
    )

    out = await meta.call_tool(
        "impo_get_norma", {"tipo": "ley", "numero": "99999", "anio": 1900}
    )
    assert out["error"]["code"] == "upstream_error"


@respx.mock
async def test_get_norma_caches_second_call():
    url = f"{BASE_URL}/bases/leyes/18331-2008"
    route = respx.get(url).mock(return_value=_latin1_response(_LEY_PAYLOAD))

    first = await meta.call_tool(
        "impo_get_norma", {"tipo": "ley", "numero": "18331", "anio": 2008}
    )
    second = await meta.call_tool(
        "impo_get_norma", {"tipo": "ley", "numero": "18331", "anio": 2008}
    )

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


async def test_diario_oficial_all_sections():
    out = await meta.call_tool("impo_diario_oficial", {"fecha": "2021-11-09"})
    secs = {s["seccion"]: s["url"] for s in out["data"]["secciones"]}
    assert set(secs) == {"indice", "documentos", "avisos", "um"}
    assert secs["documentos"] == f"{BASE_URL}/diariooficial/2021/11/09/documentos.pdf"
    assert out["data"]["fecha"] == "2021-11-09"


async def test_diario_oficial_single_section_and_ddmmyyyy():
    out = await meta.call_tool(
        "impo_diario_oficial", {"fecha": "09/11/2021", "seccion": "indice"}
    )
    secciones = out["data"]["secciones"]
    assert len(secciones) == 1
    assert secciones[0]["url"] == f"{BASE_URL}/diariooficial/2021/11/09/indice.pdf"


async def test_diario_oficial_bad_date_is_validation_error():
    out = await meta.call_tool("impo_diario_oficial", {"fecha": "not-a-date"})
    assert out["error"]["code"] == "validation_error"


@respx.mock
async def test_buscar_resolves_when_number_year_parseable():
    url = f"{BASE_URL}/bases/leyes/18331-2008"
    route = respx.get(url).mock(return_value=_latin1_response(_LEY_PAYLOAD))

    out = await meta.call_tool(
        "impo_buscar_normativa", {"query": "ley 18331/2008 datos personales"}
    )

    assert route.called
    assert out["data"]["resuelto"] is True
    assert out["data"]["nombreNorma"] == "Protección de Datos Personales"


async def test_buscar_degrades_to_search_urls():
    out = await meta.call_tool(
        "impo_buscar_normativa", {"query": "protección de datos"}
    )
    data = out["data"]
    assert data["status"] == "partial"
    assert data["resuelto"] is False
    assert out["_meta"]["degraded"] is True
    urls = [u["url"] for u in data["urls_busqueda"]]
    assert any("/?s=" in u for u in urls)


def test_module_prompts_registered():
    names = {p.name for p in registry.prompts() if p.module == "impo"}
    assert {
        "impo_consultar_norma",
        "impo_diario_del_dia",
        "impo_buscar_normativa_guia",
    } <= names


def test_module_resources_registered():
    uris = {r.uri for r in registry.resources() if r.module == "impo"}
    assert {"uru://impo/guia-de-uso", "uru://impo/esquema"} <= uris


def test_prompt_text_references_real_tools():
    by_name = {p.name: p for p in registry.prompts()}
    assert "impo_get_norma" in by_name["impo_consultar_norma"].handler(
        tipo="ley", numero="18331", anio="2008"
    )
    assert "impo_diario_oficial" in by_name["impo_diario_del_dia"].handler()
