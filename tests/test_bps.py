"""Unit tests for the BPS (Observatorio / BPS en Cifras) module, HTTP mocked."""

from __future__ import annotations

import base64
import io
import zipfile

import httpx
import pytest
import respx

import uruguay_mcp.modules.bps  # noqa: F401
from uruguay_mcp.meta import tools as meta
from uruguay_mcp.modules.bps.constants import BASE_URL, MODULE
from uruguay_mcp.shared import cache, http
from uruguay_mcp.shared.registry import registry


@pytest.fixture(autouse=True)
async def _clean():
    cache.clear()
    yield
    cache.clear()
    await http.aclose()


def _hits(*sources: dict) -> list[dict]:
    return [{"_index": "i", "_source": s} for s in sources]


def _build_zip_b64(files: dict[str, str | bytes]) -> str:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _fake_xlsx(rows: list[list[str]]) -> bytes:
    """Build a minimal XLSX (inline strings) — what BPS serves named '.csv'."""
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

    def _ref(ci: int, ri: int) -> str:
        col, n = "", ci + 1
        while n:
            n, r = divmod(n - 1, 26)
            col = chr(65 + r) + col
        return f"{col}{ri}"

    xml_rows = ""
    for ri, row in enumerate(rows, 1):
        cells = "".join(
            f'<c r="{_ref(ci, ri)}" t="inlineStr"><is><t>{v}</t></is></c>'
            for ci, v in enumerate(row)
        )
        xml_rows += f'<row r="{ri}">{cells}</row>'
    sheet = (
        f'<?xml version="1.0"?><worksheet xmlns="{ns}">'
        f"<sheetData>{xml_rows}</sheetData></worksheet>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue()


@respx.mock
async def test_listar_categorias_drops_test_nodes_by_default():
    payload = _hits(
        {"id": 6, "id_padre": 1, "orden": 1, "nombre": "Jubilaciones"},
        {"id": 7, "id_padre": 1, "orden": 2, "nombre": "Pensiones sobrevivencia"},
        {"id": 99, "id_padre": 1, "orden": 3, "nombre": "Pagina de Prueba"},
        {"id": 100, "id_padre": 1, "orden": 4, "nombre": "Día internacional de la mujer"},
    )
    route = respx.post(f"{BASE_URL}/menu").mock(return_value=httpx.Response(200, json=payload))

    out = await meta.call_tool("bps_listar_categorias", {})

    assert route.called
    assert out["_meta"]["source"]["api"] == "observatorio.bps.gub.uy"
    body = out["data"]
    nombres = {c["nombre"] for c in body["categorias"]}
    assert nombres == {"Jubilaciones", "Pensiones sobrevivencia"}
    assert body["total_nodos"] == 4
    assert body["devueltos"] == 2
    assert body["filtro_pruebas_aplicado"] is True


@respx.mock
async def test_listar_categorias_incluir_pruebas_returns_all():
    payload = _hits(
        {"id": 6, "id_padre": 1, "orden": 1, "nombre": "Jubilaciones"},
        {"id": 99, "id_padre": 1, "orden": 3, "nombre": "Pagina de Prueba"},
    )
    respx.post(f"{BASE_URL}/menu").mock(return_value=httpx.Response(200, json=payload))

    out = await meta.call_tool("bps_listar_categorias", {"incluir_pruebas": True})
    body = out["data"]
    assert body["devueltos"] == 2
    assert body["filtro_pruebas_aplicado"] is False


@respx.mock
async def test_listar_paneles():
    payload = _hits(
        {"id": 1, "nombre": "Prestaciones", "bloques": [2, 3], "previsualizaion": "x"},
        {"id": 2, "nombre": "Recaudación", "bloques": [10]},
    )
    route = respx.post(f"{BASE_URL}/panel").mock(return_value=httpx.Response(200, json=payload))

    out = await meta.call_tool("bps_listar_paneles", {})

    assert route.called
    body = out["data"]
    assert body["total"] == 2
    assert body["paneles"][0] == {"id": 1, "nombre": "Prestaciones", "bloques": [2, 3]}


@respx.mock
async def test_indicador_slims_columns_rows_and_caps_datos():
    datos = [
        {"Departamento": "Total", "Valor": 518765, "Importe $": 20074584328},
        {"Departamento": "Montevideo", "Valor": 200000, "Importe $": 1000},
        {"Departamento": "Canelones", "Valor": 100000, "Importe $": 500},
    ]
    payload = _hits(
        {
            "nombre": "Jubilaciones",
            "descripcion": "Pasividades por jubilación",
            "id_menu": 6,
            "id_pagina": 1,
            "id_bloque": 2,
            "id_tipo_de_indicador": 4,
            "datos": datos,
            "archivosSeries": [{"nombre": "jub.csv", "tamanio": 100, "fechaUpload": "06/03/2024"}],
            "filtroDatosSexo": True,
            "filtroDatosDepartamento": None,
        }
    )
    route = respx.post(f"{BASE_URL}/instancia_de_indicador").mock(
        return_value=httpx.Response(200, json=payload)
    )

    out = await meta.call_tool("bps_indicador", {"bloque": 2, "max_filas": 2})

    assert route.called
    body = out["data"]
    assert body["encontrado"] is True
    assert body["nombre"] == "Jubilaciones"
    assert body["columnas"] == ["Departamento", "Valor", "Importe $"]
    assert body["n_filas"] == 3
    assert len(body["datos"]) == 2
    assert body["tiene_filtro_sexo"] is True
    assert body["tiene_filtro_departamento"] is False
    # Confirm the request body carried the correct contract.
    req = route.calls.last.request
    import json

    assert json.loads(req.content) == {"pagina": 1, "bloque": 2, "filtro": None}


@respx.mock
async def test_indicador_empty_returns_encontrado_false():
    respx.post(f"{BASE_URL}/instancia_de_indicador").mock(
        return_value=httpx.Response(200, json=[])
    )

    out = await meta.call_tool("bps_indicador", {"bloque": 9999})
    body = out["data"]
    assert body == {"encontrado": False, "bloque": 9999}


@respx.mock
async def test_indicador_error_envelope_becomes_upstream_error():
    respx.post(f"{BASE_URL}/instancia_de_indicador").mock(
        return_value=httpx.Response(200, json={"error": "500"})
    )

    out = await meta.call_tool("bps_indicador", {"bloque": 2})
    assert out["error"]["code"] == "upstream_error"


@respx.mock
async def test_buscar_indicador_matches_by_query():
    panel = _hits({"id": 1, "nombre": "Prestaciones", "bloques": [2, 3]})
    respx.post(f"{BASE_URL}/panel").mock(return_value=httpx.Response(200, json=panel))

    def _ind(request):
        import json

        bloque = json.loads(request.content)["bloque"]
        if bloque == 2:
            return httpx.Response(
                200,
                json=_hits(
                    {
                        "nombre": "Jubilaciones",
                        "descripcion": "pasividades",
                        "id_menu": 6,
                        "id_pagina": 1,
                        "datos": [],
                        "archivosSeries": [
                            {"nombre": "a.csv", "fechaUpload": "01/01/2023"},
                            {"nombre": "b.csv", "fechaUpload": "06/03/2024"},
                        ],
                    }
                ),
            )
        return httpx.Response(
            200,
            json=_hits(
                {
                    "nombre": "Recaudación",
                    "descripcion": "ingresos",
                    "id_menu": 10,
                    "id_pagina": 5,
                    "datos": [],
                    "archivosSeries": [],
                }
            ),
        )

    respx.post(f"{BASE_URL}/instancia_de_indicador").mock(side_effect=_ind)

    out = await meta.call_tool("bps_buscar_indicador", {"query": "jubilaciones"})
    body = out["data"]
    assert body["total"] == 1
    res = body["resultados"][0]
    assert res["bloque"] == 2
    assert res["pagina"] == 1
    assert res["nombre"] == "Jubilaciones"
    # Latest fechaUpload surfaced.
    assert res["fechaUpload"] == "06/03/2024"


@respx.mock
async def test_serie_csv_parses_xlsx_disguised_as_csv():
    # BPS serves XLSX workbooks named '.csv'; the tool must parse them to rows.
    xlsx = _fake_xlsx(
        [["Departamento", "Valor"], ["Total", "518765"], ["Salto", "7000"]]
    )
    b64 = _build_zip_b64(
        {
            "Inicio/3-serie-Jubilaciones e importe.csv": xlsx,
            "Inicio/otra.csv": _fake_xlsx([["A"], ["1"]]),
        }
    )
    route = respx.get(f"{BASE_URL}/series_por_paginas").mock(
        return_value=httpx.Response(200, json={"zip": b64})
    )

    out = await meta.call_tool(
        "bps_serie_csv", {"id_pagina": 1, "nombre": "jubilaciones"}
    )

    assert route.called
    body = out["data"]
    assert body["total_archivos"] == 1
    archivo = body["archivos"][0]
    assert archivo["formato"] == "xlsx"
    assert archivo["columnas"] == ["Departamento", "Valor"]
    assert archivo["n_filas"] == 2
    assert archivo["filas"][0] == {"Departamento": "Total", "Valor": "518765"}


@respx.mock
async def test_serie_csv_parses_plain_csv_and_caps_rows():
    b64 = _build_zip_b64({"a.csv": "col\n1\n2\n3\n", "b.csv": "col\nx\n"})
    respx.get(f"{BASE_URL}/series_por_paginas").mock(
        return_value=httpx.Response(200, json={"zip": b64})
    )

    out = await meta.call_tool("bps_serie_csv", {"id_pagina": 1, "max_filas": 2})
    body = out["data"]
    assert body["total_archivos"] == 2
    a = next(x for x in body["archivos"] if x["nombre"] == "a.csv")
    assert a["formato"] == "csv"
    assert a["columnas"] == ["col"]
    # max_filas=2 keeps header + 2 data rows.
    assert a["n_filas"] == 2


@respx.mock
async def test_serie_csv_bad_zip_becomes_upstream_error():
    bad = base64.b64encode(b"not a zip").decode("ascii")
    respx.get(f"{BASE_URL}/series_por_paginas").mock(
        return_value=httpx.Response(200, json={"zip": bad})
    )

    out = await meta.call_tool("bps_serie_csv", {"id_pagina": 1})
    assert out["error"]["code"] == "upstream_error"


@respx.mock
async def test_menu_cache():
    payload = _hits({"id": 6, "id_padre": 1, "orden": 1, "nombre": "Jubilaciones"})
    route = respx.post(f"{BASE_URL}/menu").mock(return_value=httpx.Response(200, json=payload))

    first = await meta.call_tool("bps_listar_categorias", {})
    second = await meta.call_tool("bps_listar_categorias", {})

    assert first["_meta"]["cached"] is False
    assert second["_meta"]["cached"] is True
    assert route.call_count == 1


def test_bps_prompts_registered():
    by_name = {p.name: p for p in registry.prompts()}
    expected = {"bps_pasividades_actuales", "bps_consultar_indicador"}
    assert expected <= set(by_name)
    for name in expected:
        spec = by_name[name]
        assert spec.module == MODULE
        assert spec.description


def test_bps_resources_registered():
    by_uri = {r.uri: r for r in registry.resources()}
    expected = {"uru://bps/catalogo-indicadores", "uru://bps/flujo-api"}
    assert expected <= set(by_uri)
    for uri in expected:
        spec = by_uri[uri]
        assert spec.module == MODULE
        assert spec.uri.startswith("uru://bps/")
        assert spec.mime_type == "text/markdown"


def test_bps_prompt_handlers_return_strings():
    by_name = {p.name: p for p in registry.prompts()}
    text = by_name["bps_pasividades_actuales"].handler(tema="pensiones")
    assert isinstance(text, str)
    assert "bps_buscar_indicador" in text
    assert "bps_indicador" in text


def test_bps_resource_handlers_return_strings():
    by_uri = {r.uri: r for r in registry.resources()}
    text = by_uri["uru://bps/flujo-api"].handler()
    assert isinstance(text, str)
    assert "bps_indicador" in text
    assert "bps_serie_csv" in text


@pytest.mark.integration
async def test_menu_live_returns_nonempty_list():
    from uruguay_mcp.modules.bps import client

    hits, _, _ = await client.post_hits("menu", {})
    assert isinstance(hits, list)
    assert len(hits) > 0
