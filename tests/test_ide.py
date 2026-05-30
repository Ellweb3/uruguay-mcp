"""Unit tests for the IDE Uruguay module, with the HTTP layer mocked."""

from __future__ import annotations

import httpx
import pytest
import respx

import uruguay_mcp.modules.ide  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.ide.constants import (
    GEO_CANDIDATES_URL,
    GEO_DIRECUNICA_URL,
    GEO_REVERSE_URL,
    WFS_URL,
)
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry

CAPABILITIES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:WFS_Capabilities version="2.0.0"
    xmlns:wfs="http://www.opengis.net/wfs/2.0">
  <wfs:FeatureTypeList>
    <wfs:FeatureType>
      <wfs:Name>ET_CATASTRO:parcelario_urbano</wfs:Name>
      <wfs:Title>Parcelario urbano</wfs:Title>
    </wfs:FeatureType>
    <wfs:FeatureType>
      <wfs:Name>ws_catastro:departamentos</wfs:Name>
      <wfs:Title>Departamentos</wfs:Title>
    </wfs:FeatureType>
    <wfs:FeatureType>
      <wfs:Name>ideuy:ejes_de_calle_ide_</wfs:Name>
      <wfs:Title>Ejes de calle</wfs:Title>
    </wfs:FeatureType>
  </wfs:FeatureTypeList>
</wfs:WFS_Capabilities>
"""

FEATURE_COLLECTION = {
    "type": "FeatureCollection",
    "totalFeatures": 1,
    "numberMatched": 1,
    "numberReturned": 1,
    "features": [
        {
            "type": "Feature",
            "id": "parcelario_urbano.1",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-56.20, -34.91],
                        [-56.19, -34.91],
                        [-56.19, -34.90],
                        [-56.20, -34.90],
                        [-56.20, -34.91],
                    ]
                ],
            },
            "properties": {
                "padron": 1234,
                "depto": "MONTEVIDEO",
                "localidad": "MONTEVIDEO",
                "manzana": "10",
                "area": 250.5,
            },
        }
    ],
}

GEO_ITEMS = [
    {
        "type": "CALLEyPORTAL",
        "address": "AVENIDA 18 DE JULIO 1234",
        "nomVia": "AVENIDA 18 DE JULIO",
        "portalNumber": "1234",
        "departamento": "MONTEVIDEO",
        "localidad": "MONTEVIDEO",
        "postalCode": "11200",
        "lat": -34.9059,
        "lng": -56.1913,
    }
]


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


@respx.mock
async def test_listar_capas_parses_and_filters():
    route = respx.get(WFS_URL).mock(return_value=httpx.Response(200, text=CAPABILITIES_XML))

    out = await meta.call_tool("ide_listar_capas", {"filtro": "catastro"})

    assert route.called
    assert out["_meta"]["source"]["api"] == "mapas.ide.uy/wfs"
    body = out["data"]
    names = {c["typeNames"] for c in body["capas"]}
    assert names == {"ET_CATASTRO:parcelario_urbano", "ws_catastro:departamentos"}
    first = next(c for c in body["capas"] if c["typeNames"].startswith("ET_CATASTRO"))
    assert first["workspace"] == "ET_CATASTRO"
    assert "title" not in first  # incluir_titulos defaults to false


@respx.mock
async def test_listar_capas_caches_second_call():
    route = respx.get(WFS_URL).mock(return_value=httpx.Response(200, text=CAPABILITIES_XML))

    first = await meta.call_tool("ide_listar_capas", {})
    second = await meta.call_tool("ide_listar_capas", {})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


@respx.mock
async def test_features_slims_geometry():
    route = respx.get(WFS_URL).mock(return_value=httpx.Response(200, json=FEATURE_COLLECTION))

    out = await meta.call_tool(
        "ide_features",
        {"capa": "ws_catastro:departamentos", "cql_filter": "depto='MONTEVIDEO'"},
    )

    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["outputFormat"] == "application/json"
    assert params["request"] == "GetFeature"
    assert params["count"] == "50"
    feat = out["data"]["features"][0]
    # slim=true -> geometry summarized, no raw coordinate arrays.
    assert feat["geometry"]["type"] == "Polygon"
    assert "bbox" in feat["geometry"]
    assert "centroid" in feat["geometry"]
    assert "coordinates" not in feat["geometry"]
    assert feat["properties"]["padron"] == 1234


@respx.mock
async def test_features_full_geometry_when_slim_false():
    respx.get(WFS_URL).mock(return_value=httpx.Response(200, json=FEATURE_COLLECTION))

    out = await meta.call_tool(
        "ide_features",
        {"capa": "ws_catastro:departamentos", "cql_filter": "1=1", "slim": False},
    )

    feat = out["data"]["features"][0]
    assert "coordinates" in feat["geometry"]


@respx.mock
async def test_features_solo_conteo_uses_hits():
    route = respx.get(WFS_URL).mock(
        return_value=httpx.Response(200, json={"numberMatched": 4242, "features": []})
    )

    out = await meta.call_tool(
        "ide_features",
        {"capa": "ET_CATASTRO:parcelario_urbano", "solo_conteo": True},
    )

    params = dict(route.calls.last.request.url.params)
    assert params["resultType"] == "hits"
    assert "count" not in params
    assert out["data"]["numberMatched"] == 4242


@respx.mock
async def test_features_bbox_gets_crs_uri():
    route = respx.get(WFS_URL).mock(return_value=httpx.Response(200, json=FEATURE_COLLECTION))

    await meta.call_tool(
        "ide_features",
        {"capa": "ws_catastro:departamentos", "bbox": "-34.91,-56.20,-34.90,-56.19"},
    )

    bbox = dict(route.calls.last.request.url.params)["bbox"]
    assert bbox.endswith("urn:ogc:def:crs:EPSG::4326")


@respx.mock
async def test_parcela_requires_bbox_or_filter():
    route = respx.get(WFS_URL).mock(return_value=httpx.Response(200, json=FEATURE_COLLECTION))

    out = await meta.call_tool("ide_parcela_catastral", {"tipo": "urbano"})

    assert out["error"]["code"] == "validation_error"
    assert not route.called


@respx.mock
async def test_parcela_builds_depto_padron_filter():
    route = respx.get(WFS_URL).mock(return_value=httpx.Response(200, json=FEATURE_COLLECTION))

    out = await meta.call_tool(
        "ide_parcela_catastral",
        {"departamento": "montevideo", "padron": 1234},
    )

    params = dict(route.calls.last.request.url.params)
    assert params["typeNames"] == "ET_CATASTRO:parcelario_urbano"
    assert params["CQL_FILTER"] == "depto='MONTEVIDEO' AND padron=1234"
    assert out["data"]["features"][0]["properties"]["padron"] == 1234


@respx.mock
async def test_geocodificar_normalizes_results():
    route = respx.get(GEO_DIRECUNICA_URL).mock(return_value=httpx.Response(200, json=GEO_ITEMS))

    out = await meta.call_tool(
        "ide_geocodificar",
        {"direccion": "AVENIDA 18 DE JULIO 1234", "limite": 2},
    )

    assert route.called
    assert out["_meta"]["source"]["api"] == "direcciones.ide.uy"
    body = out["data"]
    assert body["count"] == 1
    res = body["results"][0]
    assert res["lat"] == -34.9059
    assert res["lng"] == -56.1913
    assert res["departamento"] == "MONTEVIDEO"
    assert res["postalCode"] == "11200"


@respx.mock
async def test_geocodificar_autocompletar_uses_candidates():
    route = respx.get(GEO_CANDIDATES_URL).mock(return_value=httpx.Response(200, json=GEO_ITEMS))

    out = await meta.call_tool(
        "ide_geocodificar",
        {"direccion": "18 de jul", "autocompletar": True},
    )

    assert route.called
    assert out["data"]["count"] == 1


@respx.mock
async def test_geocodificar_inverso():
    route = respx.get(GEO_REVERSE_URL).mock(return_value=httpx.Response(200, json=GEO_ITEMS))

    out = await meta.call_tool(
        "ide_geocodificar_inverso",
        {"latitud": -34.9059, "longitud": -56.1913, "limite": 1},
    )

    assert route.called
    params = dict(route.calls.last.request.url.params)
    assert params["latitud"] == "-34.9059"
    assert params["longitud"] == "-56.1913"
    assert out["data"]["results"][0]["address"] == "AVENIDA 18 DE JULIO 1234"


@respx.mock
async def test_wfs_failure_becomes_error_envelope():
    respx.get(WFS_URL).mock(return_value=httpx.Response(500, text="boom"))

    out = await meta.call_tool("ide_listar_capas", {})
    assert out["error"]["code"] == "upstream_error"


def test_module_prompts_registered():
    names = {p.name for p in registry.prompts() if p.module == "ide"}
    assert {
        "ide_buscar_capa_y_features",
        "ide_consultar_catastro",
        "ide_geocodificar_direccion",
    } <= names


def test_module_resources_registered():
    uris = {r.uri for r in registry.resources() if r.module == "ide"}
    assert {
        "uru://ide/guia-de-uso",
        "uru://ide/capas-destacadas",
    } <= uris


def test_prompt_text_references_real_tools():
    by_name = {p.name: p for p in registry.prompts()}
    text = by_name["ide_geocodificar_direccion"].handler(direccion="18 de julio 1234")
    assert "ide_geocodificar" in text
    text2 = by_name["ide_buscar_capa_y_features"].handler(tema="catastro")
    assert "ide_listar_capas" in text2
    assert "ide_features" in text2
