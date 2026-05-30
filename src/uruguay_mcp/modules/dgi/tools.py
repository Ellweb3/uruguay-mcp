"""Discoverable tools for the DGI (Dirección General Impositiva) open data.

Todo acá deriva de HTML/binarios: la DGI no expone API. Los listados de
``gub.uy`` embeben enlaces directos a archivos ``.ods``/``.xlsx``/``.csv``
(valores fiscales de referencia) y ``.pdf`` (boletines). Los anchors se extraen
con regex; las planillas se parsean con la stdlib (zipfile + ElementTree para
ODS/XLSX, csv para CSV) sin dependencias nuevas.
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from html import unescape
from typing import Any
from urllib.parse import unquote

from ...shared import errors
from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import (
    ALLOWED_HOST_PREFIX,
    API_NAME,
    MAX_PAGES,
    MAX_REPEAT,
    MAX_ROWS,
    MODULE,
    PREVIEW_ROWS,
    TABLE_EXTS,
)
from .schemas import (
    BoletinesArgs,
    BuscarValorArgs,
    ListarDatosArgs,
    TablaArgs,
)

# OpenDocument namespaces (ODS = ZIP con content.xml).
_ODS_TABLE = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
_ODS_TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
_ODS_OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"

# Worksheet/sharedStrings viven en el namespace SpreadsheetML (XLSX).
_XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# Un anchor de descarga. El href puede venir con comillas dobles o simples
# (el sitio usa href='...' en los enlaces de descarga). El título legible suele
# estar en aria-label="Descargar: <titulo> (.ods 19 KB)" más que en el cuerpo.
_ANCHOR_RE = re.compile(
    r"<a\b(?P<attrs>[^>]*\bhref=(?:\"[^\"]+\"|'[^']+')[^>]*)>(?P<text>.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
_HREF_RE = re.compile(r"""href=(?:"(?P<d>[^"]+)"|'(?P<s>[^']+)')""", re.IGNORECASE)
_ARIA_RE = re.compile(
    r"""aria-label=(?:"(?P<d>[^"]*)"|'(?P<s>[^']*)')""", re.IGNORECASE
)
# Limpia el prefijo "Descargar:" y el sufijo "(.ods 19 KB)" del aria-label.
_ARIA_PREFIX_RE = re.compile(r"^\s*descargar:\s*", re.IGNORECASE)
_ARIA_SUFFIX_RE = re.compile(r"\s*\([^)]*\)\s*$")
_TAG_RE = re.compile(r"<[^>]+>")
# El segmento /files/YYYY-MM/ del path es el período de publicación.
_PERIODO_RE = re.compile(r"/files/(\d{4}-\d{2})/")
# Año de 4 dígitos (para boletines).
_ANIO_RE = re.compile(r"(20\d{2}|19\d{2})")


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def _norm(text: Any) -> str:
    """Lowercase + accent-insensitive normalization for matching."""
    return _strip_accents(str(text or "")).lower()


def _clean_text(raw: str) -> str:
    """Strip tags, collapse whitespace and unescape HTML entities."""
    text = _TAG_RE.sub(" ", raw)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _ext_of(url: str) -> str | None:
    """Lowercase file extension (without dot) of a URL path, or None."""
    path = url.split("?", 1)[0].split("#", 1)[0]
    base = path.rsplit("/", 1)[-1]
    if "." not in base:
        return None
    return base.rsplit(".", 1)[-1].lower()


def _basename_titulo(url: str) -> str:
    """Unquoted filename basename without extension, as a fallback title."""
    path = url.split("?", 1)[0].split("#", 1)[0]
    base = unquote(path.rsplit("/", 1)[-1])
    if "." in base:
        base = base.rsplit(".", 1)[0]
    return base.replace("_", " ").replace("-", " ").strip() or base


def _periodo_of(url: str) -> str | None:
    m = _PERIODO_RE.search(unquote(url))
    return m.group(1) if m else None


def _anio_of(url: str, titulo: str) -> int | None:
    """4-digit year from the filename basename or the title.

    The ``/files/YYYY-MM/`` period segment is stripped first so the publication
    period (e.g. 2025-04) is not mistaken for the bulletin's year.
    """
    base = unquote(url.split("?", 1)[0].rsplit("/", 1)[-1])
    for hay in (base, titulo):
        m = _ANIO_RE.search(hay)
        if m:
            return int(m.group(1))
    return None


def _aria_titulo(attrs: str) -> str | None:
    """Clean the title out of an aria-label='Descargar: <titulo> (.ods 19 KB)'."""
    m = _ARIA_RE.search(attrs)
    if not m:
        return None
    raw = unescape(m.group("d") if m.group("d") is not None else m.group("s") or "")
    raw = _ARIA_PREFIX_RE.sub("", raw)
    raw = _ARIA_SUFFIX_RE.sub("", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw or None


def _extract_file_anchors(html_text: str, exts: tuple[str, ...]) -> list[dict[str, Any]]:
    """Extract anchors pointing to /files/ assets with one of ``exts``.

    Returns dicts ``{titulo, url, formato, periodo}``. Titulo prefers the
    ``aria-label`` ("Descargar: <titulo> (...)"), then the anchor's visible
    text, else the unquoted filename basename. The href may use single or
    double quotes (the download links use single quotes).
    """
    out: list[dict[str, Any]] = []
    for m in _ANCHOR_RE.finditer(html_text):
        attrs = m.group("attrs")
        href_m = _HREF_RE.search(attrs)
        if not href_m:
            continue
        href = unescape(
            href_m.group("d") if href_m.group("d") is not None else href_m.group("s") or ""
        ).strip()
        if "/files/" not in href:
            continue
        ext = _ext_of(href)
        if ext is None or f".{ext}" not in exts:
            continue
        aria = _aria_titulo(attrs)
        visible = _clean_text(m.group("text"))
        if aria and len(aria) >= 3:
            titulo = aria
        elif len(visible) >= 3:
            titulo = visible
        else:
            titulo = _basename_titulo(href)
        out.append(
            {
                "titulo": titulo,
                "url": href,
                "formato": ext,
                "periodo": _periodo_of(href),
            }
        )
    return out


# --- ODS parser -----------------------------------------------------------


def _cell_text(cell: ET.Element) -> str:
    """Text of an ODS cell: its <text:p> contents, else office value/date attr."""
    parts = [
        "".join(p.itertext()) for p in cell.findall(f"{_ODS_TEXT}p")
    ]
    text = " ".join(p for p in parts if p).strip()
    if text:
        return text
    # Numbers/dates may live only as attributes.
    for attr in (f"{_ODS_OFFICE}value", f"{_ODS_OFFICE}date-value"):
        val = cell.get(attr)
        if val:
            return val
    return ""


def _expand_row(row: ET.Element) -> list[str]:
    """Expand one ODS row's cells, honouring number-columns-repeated.

    Trailing empty cells are NOT padded; any single repeat is capped at
    ``MAX_REPEAT`` before trimming so spacer runs don't blow up.
    """
    cells: list[str] = []
    for cell in row:
        tag = cell.tag
        if tag not in (f"{_ODS_TABLE}table-cell", f"{_ODS_TABLE}covered-table-cell"):
            continue
        repeat = cell.get(f"{_ODS_TABLE}number-columns-repeated")
        n = 1
        if repeat and repeat.isdigit():
            n = min(int(repeat), MAX_REPEAT)
        cells.extend([_cell_text(cell)] * max(n, 1))
    # Trim trailing empties (spreadsheet padding).
    while cells and cells[-1] == "":
        cells.pop()
    return cells


def _parse_ods_sheet(data: bytes, hoja: int, max_filas: int) -> tuple[int, list[list[str]]]:
    """Parse one sheet of an ODS blob → ``(n_hojas, rows)``.

    Rows expand number-rows-repeated (capped), skip fully-empty rows, and stop
    after ``max_filas`` non-empty rows.
    """
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        content = zf.read("content.xml")
    root = ET.fromstring(content)
    tables = list(root.iter(f"{_ODS_TABLE}table"))
    n_hojas = len(tables)
    if hoja < 0 or hoja >= n_hojas:
        raise errors.upstream(
            API_NAME, f"hoja {hoja} fuera de rango (la planilla tiene {n_hojas})"
        )
    table = tables[hoja]
    rows: list[list[str]] = []
    for row in table.findall(f"{_ODS_TABLE}table-row"):
        repeat = row.get(f"{_ODS_TABLE}number-rows-repeated")
        n = 1
        if repeat and repeat.isdigit():
            n = min(int(repeat), MAX_REPEAT)
        expanded = _expand_row(row)
        if not expanded:  # fully-empty (spacer) row → skip
            continue
        for _ in range(max(n, 1)):
            rows.append(list(expanded))
            if len(rows) >= max_filas:
                return n_hojas, rows
    return n_hojas, rows


# --- XLSX parser (mirrors bps tools.py) -----------------------------------


def _col_index(ref: str) -> int:
    """Map a cell ref like 'B5' to a 0-based column index (-1 if none)."""
    letters = "".join(ch for ch in ref if ch.isalpha())
    if not letters:
        return -1
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch.upper()) - 64)
    return n - 1


def _parse_xlsx_sheet(data: bytes, hoja: int, max_filas: int) -> tuple[int, list[list[str]]]:
    """Parse one worksheet of an XLSX blob → ``(n_hojas, rows)``."""
    with zipfile.ZipFile(io.BytesIO(data)) as xz:
        names = xz.namelist()
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            sroot = ET.fromstring(xz.read("xl/sharedStrings.xml"))
            for si in sroot:
                shared.append("".join(t.text or "" for t in si.iter(f"{_XLSX_NS}t")))
        sheets = sorted(
            n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
        )
        n_hojas = len(sheets)
        if hoja < 0 or hoja >= n_hojas:
            raise errors.upstream(
                API_NAME, f"hoja {hoja} fuera de rango (la planilla tiene {n_hojas})"
            )
        root = ET.fromstring(xz.read(sheets[hoja]))
        sheet_data = root.find(f"{_XLSX_NS}sheetData")
        rows: list[list[str]] = []
        for row_el in sheet_data if sheet_data is not None else []:
            by_col: dict[int, str] = {}
            max_c = -1
            for i, c in enumerate(row_el):
                ci = _col_index(c.get("r") or "")
                if ci < 0:
                    ci = i
                ctype = c.get("t")
                v = c.find(f"{_XLSX_NS}v")
                if ctype == "s" and v is not None and v.text is not None:
                    idx = int(v.text)
                    val = shared[idx] if 0 <= idx < len(shared) else ""
                elif ctype == "inlineStr":
                    is_el = c.find(f"{_XLSX_NS}is")
                    val = (
                        "".join(t.text or "" for t in is_el.iter(f"{_XLSX_NS}t"))
                        if is_el is not None
                        else ""
                    )
                else:
                    val = v.text if v is not None and v.text is not None else ""
                by_col[ci] = val
                max_c = max(max_c, ci)
            fila = [by_col.get(i, "") for i in range(max_c + 1)]
            while fila and fila[-1] == "":
                fila.pop()
            if not fila:  # fully-empty row → skip
                continue
            rows.append(fila)
            if len(rows) >= max_filas:
                break
        return n_hojas, rows


def _parse_csv(data: bytes, max_filas: int) -> tuple[int, list[list[str]]]:
    """Parse a CSV blob → ``(1, rows)`` (one logical sheet)."""
    text = data.decode("utf-8", errors="replace")
    rows: list[list[str]] = []
    for raw in csv.reader(io.StringIO(text)):
        fila = list(raw)
        while fila and fila[-1] == "":
            fila.pop()
        if not fila:
            continue
        rows.append(fila)
        if len(rows) >= max_filas:
            break
    return 1, rows


def _parse_tabla(
    data: bytes, formato: str, hoja: int, max_filas: int
) -> tuple[int, list[list[str]]]:
    """Dispatch to the right parser by ``formato`` (ods/xlsx/csv)."""
    try:
        if formato == "ods":
            return _parse_ods_sheet(data, hoja, max_filas)
        if formato == "xlsx":
            return _parse_xlsx_sheet(data, hoja, max_filas)
        return _parse_csv(data, max_filas)
    except (zipfile.BadZipFile, ET.ParseError, KeyError, ValueError) as exc:
        raise errors.upstream(API_NAME, f"no se pudo parsear el archivo {formato}") from exc


async def _collect_datos() -> tuple[list[dict[str, Any]], bool, str]:
    """Loop /datos pages, dedupe file anchors, stop when no new files appear."""
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    all_cached = True
    last_url = ""
    for page in range(MAX_PAGES):
        html_text, cached, last_url = await client.fetch_datos_page(page)
        all_cached = all_cached and cached
        anchors = _extract_file_anchors(html_text, TABLE_EXTS)
        added = 0
        for a in anchors:
            if a["url"] in seen:
                continue
            seen.add(a["url"])
            results.append(a)
            added += 1
        if added == 0:  # página sin archivos nuevos → fin
            break
    return results, all_cached, last_url


# --- Tools ----------------------------------------------------------------


@tool(
    name="dgi_listar_datos",
    module=MODULE,
    summary=(
        "Listar los archivos de valores fiscales de referencia que publica la "
        "DGI (Unidad Indexada, IPC, cotizaciones, coeficientes ITP/activo fijo, "
        "tasas de recargos Art.94 y facilidades Art.33). La DGI no expone API: "
        "los archivos .ods/.xlsx/.csv se extraen de los enlaces del HTML de "
        "gub.uy. Filtrá por tema y/o formato. Usá dgi_tabla con la url para "
        "leer su contenido."
    ),
    params_model=ListarDatosArgs,
    keywords=[
        "dgi",
        "impuestos",
        "tributario",
        "valores",
        "referencia",
        "unidad indexada",
        "ipc",
        "recargos",
        "itp",
        "ods",
        "planilla",
    ],
)
async def listar_datos(
    tema: str | None = None, formato: str | None = None
) -> dict[str, Any]:
    results, cached, url = await _collect_datos()
    if tema:
        needle = _norm(tema)
        results = [r for r in results if needle in _norm(r["titulo"])]
    if formato:
        fmt = formato.lstrip(".").lower()
        results = [r for r in results if r["formato"] == fmt]
    return envelope(
        {
            "total": len(results),
            "results": results,
            "nota": (
                "La DGI no publica una API: estos archivos (valores fiscales de "
                "referencia) se extraen de los enlaces de descarga del HTML de "
                "gub.uy. Pasá la 'url' a dgi_tabla para leer la planilla."
            ),
        },
        api=API_NAME,
        url=url,
        cached=cached if results else False,
    )


@tool(
    name="dgi_tabla",
    module=MODULE,
    summary=(
        "Descargar y parsear una planilla de valores de la DGI (.ods/.xlsx/.csv) "
        "a filas tabuladas. Los .ods suelen tener varias hojas; elegí 'hoja'. No "
        "asume encabezado (hay filas de título/relleno): devuelve filas crudas "
        "(listas de celdas) para que el modelo las interprete. La url debe ser "
        "de www.gub.uy y terminar en .ods/.xlsx/.csv."
    ),
    params_model=TablaArgs,
    keywords=[
        "dgi",
        "tabla",
        "planilla",
        "ods",
        "xlsx",
        "csv",
        "hoja",
        "valores",
        "leer",
        "parsear",
    ],
)
async def tabla(url: str, hoja: int = 0, max_filas: int = MAX_ROWS) -> dict[str, Any]:
    if not url.startswith(ALLOWED_HOST_PREFIX):
        raise errors.upstream(API_NAME, "url no permitida")
    ext = _ext_of(url)
    if ext is None or f".{ext}" not in TABLE_EXTS:
        raise errors.upstream(API_NAME, "url no permitida")
    data, cached, fetched_url = await client.fetch_archivo(url)
    n_hojas, filas = _parse_tabla(data, ext, hoja, max_filas)
    return envelope(
        {
            "url": url,
            "formato": ext,
            "hoja": hoja,
            "n_hojas": n_hojas,
            "n_filas": len(filas),
            "filas": filas,
        },
        api=API_NAME,
        url=fetched_url,
        cached=cached,
    )


@tool(
    name="dgi_buscar_valor",
    module=MODULE,
    summary=(
        "Buscar un valor fiscal de referencia de la DGI por tema y traer su "
        "tabla. Recorre el listado, elige la mejor coincidencia por título "
        "(prefiriendo el período más reciente) y parsea la hoja 0 devolviendo "
        "una vista previa de filas. Ideal para 'unidad indexada', 'IPC', "
        "'recargos por mora', 'coeficiente ITP'."
    ),
    params_model=BuscarValorArgs,
    keywords=[
        "dgi",
        "buscar",
        "valor",
        "referencia",
        "unidad indexada",
        "ipc",
        "recargos",
        "mora",
        "itp",
        "tributario",
    ],
)
async def buscar_valor(query: str, max_filas: int = PREVIEW_ROWS) -> dict[str, Any]:
    results, cached, list_url = await _collect_datos()
    needle = _norm(query)
    matches = [r for r in results if needle in _norm(r["titulo"])]
    if not matches:
        return envelope(
            {"encontrado": False, "query": query},
            api=API_NAME,
            url=list_url,
            cached=cached,
        )
    # Preferir el período (YYYY-MM) más reciente entre las coincidencias.
    best = max(matches, key=lambda r: r.get("periodo") or "")
    ext = _ext_of(best["url"]) or ""
    data, fcached, furl = await client.fetch_archivo(best["url"])
    n_hojas, filas = _parse_tabla(data, ext, 0, max_filas)
    return envelope(
        {
            "encontrado": True,
            "titulo": best["titulo"],
            "url": best["url"],
            "periodo": best.get("periodo"),
            "formato": ext,
            "n_hojas": n_hojas,
            "n_filas": len(filas),
            "filas": filas,
        },
        api=API_NAME,
        url=furl,
        cached=cached and fcached,
    )


@tool(
    name="dgi_boletines",
    module=MODULE,
    summary=(
        "Listar los boletines estadísticos (PDF) que publica la DGI, y "
        "opcionalmente los PDFs de gasto tributario (incluir_gasto=True). "
        "Devuelve título, año, url y categoría. No descarga ni parsea el PDF: "
        "sólo los enlaces extraídos del HTML de gub.uy."
    ),
    params_model=BoletinesArgs,
    keywords=[
        "dgi",
        "boletin",
        "estadistico",
        "estadisticas",
        "gasto tributario",
        "pdf",
        "recaudacion",
        "informe",
    ],
)
async def boletines(incluir_gasto: bool = False) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    html_text, cached, url = await client.fetch_boletines()
    for a in _extract_file_anchors(html_text, (".pdf",)):
        if a["url"] in seen:
            continue
        seen.add(a["url"])
        results.append(
            {
                "titulo": a["titulo"],
                "anio": _anio_of(a["url"], a["titulo"]),
                "url": a["url"],
                "categoria": "boletin",
            }
        )

    all_cached = cached
    last_url = url
    if incluir_gasto:
        gasto_html, gcached, gurl = await client.fetch_gasto_tributario()
        all_cached = all_cached and gcached
        last_url = gurl
        for a in _extract_file_anchors(gasto_html, (".pdf",)):
            if a["url"] in seen:
                continue
            seen.add(a["url"])
            results.append(
                {
                    "titulo": a["titulo"],
                    "anio": _anio_of(a["url"], a["titulo"]),
                    "url": a["url"],
                    "categoria": "gasto",
                }
            )

    return envelope(
        {"total": len(results), "results": results},
        api=API_NAME,
        url=last_url,
        cached=all_cached if results else False,
    )
