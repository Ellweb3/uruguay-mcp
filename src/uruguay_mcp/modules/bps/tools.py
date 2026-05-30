"""Discoverable tools for the BPS 'Observatorio / BPS en Cifras' dashboard."""

from __future__ import annotations

import base64
import binascii
import csv
import io
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from typing import Any

from ...shared import cache, errors
from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import API_NAME, MAX_DISCOVERY, MAX_ROWS, MODULE
from .schemas import (
    BuscarIndicadorArgs,
    IndicadorArgs,
    ListarCategoriasArgs,
    ListarPanelesArgs,
    SerieCsvArgs,
)

# Nodes whose nombre matches this are test/commemorative noise in /menu.
_TEST_NODE_RE = re.compile(
    r"prueba|p[aá]gina de prueba|^d[ií]a (del|de la|de las|internacional|mundial)\b",
    re.IGNORECASE,
)

# Cap series files returned by bps_serie_csv so a single call stays small.
_MAX_SERIE_FILES = 5

# Worksheet/sharedStrings live in the SpreadsheetML namespace.
_XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _col_index(ref: str) -> int:
    """Map a cell ref like 'B5' to a 0-based column index (-1 if none)."""
    letters = "".join(ch for ch in ref if ch.isalpha())
    if not letters:
        return -1
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def _parse_xlsx_rows(data: bytes, max_filas: int) -> list[list[Any]]:
    """Parse the first worksheet of an XLSX blob into rows (header + data).

    The BPS 'series' files are XLSX workbooks misnamed ``.csv``. Only the
    stdlib is used: read ``xl/sharedStrings.xml`` (if present) and the first
    ``xl/worksheets/sheetN.xml``, honouring cell refs so sparse cells align.
    """
    with zipfile.ZipFile(io.BytesIO(data)) as xz:
        names = xz.namelist()
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            sroot = ET.fromstring(xz.read("xl/sharedStrings.xml"))
            for si in sroot:
                shared.append("".join(t.text or "" for t in si.iter(f"{_XLSX_NS}t")))
        sheet = next(
            (n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")),
            None,
        )
        if sheet is None:
            return []
        root = ET.fromstring(xz.read(sheet))
        sheet_data = root.find(f"{_XLSX_NS}sheetData")
        rows: list[list[Any]] = []
        for row_el in sheet_data if sheet_data is not None else []:
            by_col: dict[int, Any] = {}
            max_c = -1
            for i, c in enumerate(row_el):
                ci = _col_index(c.get("r") or "")
                if ci < 0:
                    ci = i
                ctype = c.get("t")
                v = c.find(f"{_XLSX_NS}v")
                if ctype == "s" and v is not None and v.text is not None:
                    idx = int(v.text)
                    val: Any = shared[idx] if 0 <= idx < len(shared) else ""
                elif ctype == "inlineStr":
                    is_el = c.find(f"{_XLSX_NS}is")
                    val = (
                        "".join(t.text or "" for t in is_el.iter(f"{_XLSX_NS}t"))
                        if is_el is not None
                        else ""
                    )
                else:
                    val = v.text if v is not None else None
                by_col[ci] = val
                max_c = max(max_c, ci)
            rows.append([by_col.get(i) for i in range(max_c + 1)])
            if len(rows) > max_filas:  # header + max_filas data rows
                break
        return rows


def _rows_to_records(rows: list[list[Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    """Split parsed rows into a header list and a list of row dicts."""
    if not rows:
        return [], []
    header = [str(x) if x is not None else "" for x in rows[0]]
    records: list[dict[str, Any]] = []
    for r in rows[1:]:
        records.append({header[i]: r[i] for i in range(min(len(header), len(r)))})
    return header, records


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def _norm(text: Any) -> str:
    """Lowercase + accent-insensitive normalization for matching."""
    return _strip_accents(str(text or "")).lower()


def _slim_categoria(src: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": src.get("id"),
        "id_padre": src.get("id_padre"),
        "orden": src.get("orden"),
        "nombre": src.get("nombre"),
    }


def _slim_panel(src: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": src.get("id"),
        "nombre": src.get("nombre"),
        "bloques": src.get("bloques") or [],
    }


def _latest_fecha_upload(archivos: list[dict[str, Any]] | None) -> str | None:
    """Return the most recent fechaUpload (dd/mm/yyyy) among archivosSeries."""
    fechas = [str(a["fechaUpload"]) for a in (archivos or []) if a.get("fechaUpload")]
    if not fechas:
        return None

    def _key(f: str) -> tuple[int, int, int]:
        parts = str(f).split("/")
        if len(parts) == 3:
            d, m, y = parts
            if d.isdigit() and m.isdigit() and y.isdigit():
                return (int(y), int(m), int(d))
        return (0, 0, 0)

    return max(fechas, key=_key)


@tool(
    name="bps_listar_categorias",
    module=MODULE,
    summary=(
        "Listar el árbol de categorías/indicadores del Observatorio del BPS "
        "(/menu). Por defecto descarta nodos de prueba y conmemorativos; "
        "incluir_pruebas=True devuelve todos."
    ),
    params_model=ListarCategoriasArgs,
    keywords=[
        "bps",
        "observatorio",
        "menu",
        "categorias",
        "arbol",
        "indicadores",
        "jubilaciones",
        "pensiones",
        "previsional",
        "pasividades",
    ],
)
async def listar_categorias(incluir_pruebas: bool = False) -> dict[str, Any]:
    hits, cached, url = await client.post_hits("menu", {})
    nodos = [_slim_categoria(s) for s in hits]
    total = len(nodos)
    if not incluir_pruebas:
        nodos = [n for n in nodos if not _TEST_NODE_RE.search(str(n.get("nombre") or ""))]
    return envelope(
        {
            "total_nodos": total,
            "devueltos": len(nodos),
            "filtro_pruebas_aplicado": not incluir_pruebas,
            "nota": (
                "Se descartaron nodos de prueba/conmemorativos (nombre con "
                "'Prueba', 'Día internacional...', etc.). Usá incluir_pruebas=True "
                "para verlos todos."
                if not incluir_pruebas
                else "Se incluyen todos los nodos, incluidos los de prueba."
            ),
            "categorias": nodos,
        },
        api=API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="bps_listar_paneles",
    module=MODULE,
    summary=(
        "Listar los paneles del Observatorio del BPS (/panel). Cada panel agrupa "
        "ids de bloques; esos bloques se consultan con bps_indicador."
    ),
    params_model=ListarPanelesArgs,
    keywords=[
        "bps",
        "observatorio",
        "panel",
        "paneles",
        "bloques",
        "dashboard",
        "indicadores",
    ],
)
async def listar_paneles() -> dict[str, Any]:
    hits, cached, url = await client.post_hits("panel", {})
    paneles = [_slim_panel(s) for s in hits]
    return envelope(
        {"total": len(paneles), "paneles": paneles},
        api=API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="bps_indicador",
    module=MODULE,
    summary=(
        "Obtener un indicador del Observatorio del BPS por su bloque "
        "(/instancia_de_indicador): nombre, descripción, columnas, número de "
        "filas y los datos de la serie (jubilaciones, pensiones, recaudación, "
        "cotizantes, ...). Es la herramienta principal del módulo."
    ),
    params_model=IndicadorArgs,
    keywords=[
        "bps",
        "observatorio",
        "indicador",
        "bloque",
        "serie",
        "datos",
        "jubilaciones",
        "pensiones",
        "recaudacion",
        "cotizantes",
        "pasividades",
    ],
)
async def indicador(bloque: int, pagina: int = 1, max_filas: int = MAX_ROWS) -> dict[str, Any]:
    body = {"pagina": pagina, "bloque": bloque, "filtro": None}
    hits, cached, url = await client.post_hits("instancia_de_indicador", body)
    if not hits:
        return envelope(
            {"encontrado": False, "bloque": bloque},
            api=API_NAME,
            url=url,
            cached=cached,
        )
    src = hits[0]
    datos = src.get("datos") or []
    columnas = list(datos[0].keys()) if datos else []
    return envelope(
        {
            "encontrado": True,
            "nombre": src.get("nombre"),
            "descripcion": src.get("descripcion"),
            "id_menu": src.get("id_menu"),
            "id_pagina": src.get("id_pagina"),
            "id_bloque": src.get("id_bloque"),
            "id_tipo_de_indicador": src.get("id_tipo_de_indicador"),
            "columnas": columnas,
            "n_filas": len(datos),
            "datos": datos[:max_filas],
            "archivosSeries": src.get("archivosSeries") or [],
            "tiene_filtro_sexo": bool(src.get("filtroDatosSexo")),
            "tiene_filtro_departamento": bool(src.get("filtroDatosDepartamento")),
        },
        api=API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="bps_buscar_indicador",
    module=MODULE,
    summary=(
        "Buscar indicadores del Observatorio del BPS por tema. Recorre los "
        "paneles y sus bloques y devuelve los indicadores cuyo nombre/descripción "
        "coincide con la consulta (con bloque y pagina para luego usar "
        "bps_indicador)."
    ),
    params_model=BuscarIndicadorArgs,
    keywords=[
        "bps",
        "observatorio",
        "buscar",
        "indicador",
        "tema",
        "descubrir",
        "search",
        "jubilaciones",
        "pensiones",
        "recaudacion",
    ],
)
async def buscar_indicador(query: str, max_resultados: int = 10) -> dict[str, Any]:
    needle = _norm(query)
    cache_key = f"bps:buscar:{needle}:{max_resultados}"

    async def producer() -> dict[str, Any]:
        panel_hits, _, _ = await client.post_hits("panel", {})
        bloques: list[int] = []
        seen: set[int] = set()
        for p in panel_hits:
            for b in p.get("bloques") or []:
                if isinstance(b, int) and b not in seen:
                    seen.add(b)
                    bloques.append(b)
        matches: list[dict[str, Any]] = []
        for b in bloques[:MAX_DISCOVERY]:
            if len(matches) >= max_resultados:
                break
            body = {"pagina": 1, "bloque": b, "filtro": None}
            hits, _, _ = await client.post_hits("instancia_de_indicador", body)
            if not hits:
                continue
            src = hits[0]
            haystack = _norm(src.get("nombre")) + " " + _norm(src.get("descripcion"))
            if needle and needle not in haystack:
                continue
            matches.append(
                {
                    "bloque": b,
                    "pagina": src.get("id_pagina"),
                    "nombre": src.get("nombre"),
                    "descripcion": src.get("descripcion"),
                    "id_menu": src.get("id_menu"),
                    "fechaUpload": _latest_fecha_upload(src.get("archivosSeries")),
                }
            )
        return {
            "query": query,
            "bloques_inspeccionados": min(len(bloques), MAX_DISCOVERY),
            "total": len(matches),
            "resultados": matches,
        }

    data, cached = await cache.get_or_set(cache_key, producer)
    url = f"{client.BASE_URL}/instancia_de_indicador"
    return envelope(data, api=API_NAME, url=url, cached=cached)


@tool(
    name="bps_serie_csv",
    module=MODULE,
    summary=(
        "Descargar las series de datos de una página del Observatorio del BPS "
        "(/series_por_paginas) como filas tabuladas. Los archivos vienen en un "
        "ZIP y, pese a llamarse '.csv', son planillas XLSX: se parsean y se "
        "devuelven como filas {columna: valor}. Filtrá por nombre si querés una."
    ),
    params_model=SerieCsvArgs,
    keywords=[
        "bps",
        "observatorio",
        "serie",
        "csv",
        "xlsx",
        "planilla",
        "descarga",
        "zip",
        "datos",
        "pagina",
    ],
)
async def serie_csv(
    id_pagina: int, nombre: str | None = None, max_filas: int = MAX_ROWS
) -> dict[str, Any]:
    b64, cached, url = await client.get_series_zip(id_pagina)
    try:
        raw = base64.b64decode(b64)
    except (binascii.Error, ValueError) as exc:
        raise errors.upstream(API_NAME, "base64 de series inválido") from exc

    filtro = _norm(nombre) if nombre else None
    archivos: list[dict[str, Any]] = []
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                fname = info.filename
                if filtro and filtro not in _norm(fname):
                    continue
                if len(archivos) >= _MAX_SERIE_FILES:
                    break
                blob = zf.read(info)
                try:
                    if blob[:2] == b"PK":  # XLSX disfrazado de .csv
                        formato = "xlsx"
                        rows = _parse_xlsx_rows(blob, max_filas)
                    else:
                        formato = "csv"
                        texto = blob.decode("utf-8", errors="replace")
                        rows = list(csv.reader(io.StringIO(texto)))[: max_filas + 1]
                    columnas, filas = _rows_to_records(rows)
                    archivos.append(
                        {
                            "nombre": fname,
                            "formato": formato,
                            "columnas": columnas,
                            "n_filas": len(filas),
                            "filas": filas,
                        }
                    )
                except (ET.ParseError, zipfile.BadZipFile, ValueError) as exc:
                    archivos.append(
                        {"nombre": fname, "formato": "desconocido", "error": str(exc)}
                    )
    except zipfile.BadZipFile as exc:
        raise errors.upstream(API_NAME, "ZIP de series corrupto") from exc

    return envelope(
        {
            "id_pagina": id_pagina,
            "total_archivos": len(archivos),
            "archivos": archivos,
        },
        api=API_NAME,
        url=url,
        cached=cached,
    )
