"""Discoverable tools for IMPO (normativa nacional y Diario Oficial)."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any
from urllib.parse import quote_plus

from ...shared import errors
from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import (
    API_NAME,
    BASE_URL,
    DIARIO_SECCIONES,
    MAX_ARTICULOS,
    MODULE,
    TIPO_SLUGS,
    TIPOS_CON_ORIGINAL,
)
from .schemas import BuscarNormativaArgs, DiarioOficialArgs, GetNormaArgs

# Las URLs relativas que devuelve IMPO (urlArticulo, urlVerImagen, ...) deben
# prefijarse con el host para ser utilizables.
_TAG_RE = re.compile(r"<[^>]+>")


def _abs_url(rel: str | None) -> str | None:
    if not rel:
        return rel
    if rel.startswith("http"):
        return rel
    return f"{BASE_URL}{rel}" if rel.startswith("/") else f"{BASE_URL}/{rel}"


def _strip_html(text: str | None) -> str | None:
    """Quitar etiquetas HTML embebidas (notasArticulo, titulosArticulo, ...)."""
    if not text:
        return text
    return _TAG_RE.sub("", text).strip()


def _slim_articulo(art: dict[str, Any]) -> dict[str, Any]:
    return {
        "nroArticulo": art.get("nroArticulo"),
        "secArticulo": art.get("secArticulo"),
        "tituloArticulo": _strip_html(art.get("tituloArticulo")),
        "textoArticulo": art.get("textoArticulo"),
        "urlArticulo": _abs_url(art.get("urlArticulo")),
        "notasArticulo": _strip_html(art.get("notasArticulo")),
    }


def _slim_norma(doc: dict[str, Any], max_articulos: int) -> dict[str, Any]:
    """Proyectar la respuesta de IMPO a los campos que el modelo necesita."""
    articulos = doc.get("articulos") or []
    return {
        "tipoNorma": doc.get("tipoNorma"),
        "nroNorma": doc.get("nroNorma"),
        "anioNorma": doc.get("anioNorma"),
        "nombreNorma": doc.get("nombreNorma"),
        "leyenda": doc.get("leyenda"),
        "fechaPromulgacion": doc.get("fechaPromulgacion"),
        "fechaPublicacion": doc.get("fechaPublicacion"),
        "urlVerImagen": _abs_url(doc.get("urlVerImagen")),
        "vistos": doc.get("vistos"),
        "firmantes": doc.get("firmantes"),
        "totalArticulos": len(articulos),
        "articulos": [_slim_articulo(a) for a in articulos[:max_articulos]],
    }


def _build_norma_ruta(tipo: str, numero: str | None, anio: int) -> tuple[str, str]:
    """Devolver ``(slug_base, ruta)`` validando tipo/version/numero.

    Para constitucion la ruta es ``{anio}-{anio}`` (sin numero).
    """
    if tipo == "constitucion":
        return TIPO_SLUGS["constitucion"], f"{anio}-{anio}"
    if not numero:
        raise errors.ValidationError(
            f"Falta 'numero': es obligatorio para tipo '{tipo}'."
        )
    return TIPO_SLUGS[tipo], f"{numero}-{anio}"


@tool(
    name="impo_get_norma",
    module=MODULE,
    summary=(
        "Obtener una norma nacional (ley, decreto o constitución) como JSON "
        "estructurado por tipo + número + año, vía el mecanismo ?json=true de "
        "IMPO. Devuelve metadatos y la lista de artículos con su texto."
    ),
    params_model=GetNormaArgs,
    keywords=[
        "impo",
        "norma",
        "ley",
        "decreto",
        "constitucion",
        "uruguay",
        "normativa",
        "articulo",
    ],
)
async def get_norma(
    tipo: str,
    anio: int,
    numero: str | None = None,
    version: str = "consolidada",
    max_articulos: int = MAX_ARTICULOS,
) -> dict[str, Any]:
    if tipo not in TIPO_SLUGS:
        raise errors.ValidationError(
            "tipo inválido; usá 'ley', 'decreto' o 'constitucion'."
        )
    slug, ruta = _build_norma_ruta(tipo, numero, anio)
    if version == "original":
        if tipo not in TIPOS_CON_ORIGINAL:
            raise errors.ValidationError(
                "version 'original' sólo aplica a 'ley' y 'decreto'."
            )
        slug = f"{slug}-originales"
    elif version != "consolidada":
        raise errors.ValidationError("version inválida; usá 'consolidada' u 'original'.")

    doc, cached, url = await client.get_norma(slug, ruta)
    if not isinstance(doc, dict):
        raise errors.upstream(API_NAME, "respuesta inesperada (no es un objeto)")
    return envelope(
        _slim_norma(doc, max_articulos), api=API_NAME, url=url, cached=cached
    )


def _parse_fecha(fecha: str | None) -> date:
    if not fecha:
        return date.today()
    raw = fecha.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise errors.ValidationError(
        "Fecha inválida; usá 'YYYY-MM-DD' o 'DD/MM/YYYY'."
    )


def _diario_url(d: date, seccion: str) -> str:
    return f"{BASE_URL}/diariooficial/{d.year:04d}/{d.month:02d}/{d.day:02d}/{seccion}.pdf"


@tool(
    name="impo_diario_oficial",
    module=MODULE,
    summary=(
        "Obtener el Diario Oficial de una fecha (por defecto hoy) como URLs PDF "
        "canónicas por sección (índice, documentos, avisos, último momento). El "
        "Diario Oficial no tiene API JSON: se devuelven los enlaces PDF verificados."
    ),
    params_model=DiarioOficialArgs,
    keywords=[
        "impo",
        "diario oficial",
        "diario",
        "boletin",
        "publicacion",
        "pdf",
        "hoy",
        "fecha",
        "uruguay",
    ],
)
async def diario_oficial(
    fecha: str | None = None, seccion: str = "all"
) -> dict[str, Any]:
    d = _parse_fecha(fecha)
    if seccion == "all":
        secciones = list(DIARIO_SECCIONES)
    elif seccion in DIARIO_SECCIONES:
        secciones = [seccion]
    else:
        raise errors.ValidationError(
            "seccion inválida; usá 'indice', 'documentos', 'avisos', 'um' o 'all'."
        )
    enlaces = [
        {"seccion": s, "url": _diario_url(d, s), "mime": "application/pdf"}
        for s in secciones
    ]
    data = {
        "fecha": d.isoformat(),
        "secciones": enlaces,
        "nota": (
            "El Diario Oficial es sólo PDF. Agregá ?download=true a la URL para "
            "forzar la descarga. Las secciones son fijas: indice, documentos, "
            "avisos, um (último momento)."
        ),
    }
    return envelope(data, api=API_NAME, url=_diario_url(d, secciones[0]), cached=False)


_NUM_ANIO_RE = re.compile(r"\b(\d{1,6})\s*[-/]\s*((?:19|20)\d{2})\b")
_TIPO_HINTS = {
    "ley": "ley",
    "leyes": "ley",
    "decreto": "decreto",
    "decretos": "decreto",
    "constitucion": "constitucion",
    "constitución": "constitucion",
}


def _infer_tipo(query: str) -> str | None:
    low = query.lower()
    for word, tipo in _TIPO_HINTS.items():
        if re.search(rf"\b{word}\b", low):
            return tipo
    return None


@tool(
    name="impo_buscar_normativa",
    module=MODULE,
    summary=(
        "Búsqueda best-effort de normativa en IMPO. DEGRADADO: IMPO no expone "
        "una API JSON de búsqueda, así que esta herramienta construye las URLs "
        "canónicas de búsqueda y, si la consulta identifica tipo/número/año, "
        "resuelve directo a impo_get_norma."
    ),
    params_model=BuscarNormativaArgs,
    keywords=[
        "impo",
        "buscar",
        "search",
        "normativa",
        "ley",
        "decreto",
        "uruguay",
        "find",
    ],
)
async def buscar_normativa(
    query: str = "",
    tipo: str | None = None,
    numero: str | None = None,
    anio: int | None = None,
) -> dict[str, Any]:
    # Atajo: si tenemos (o inferimos) tipo + número + año, resolvemos la norma.
    eff_tipo = tipo or _infer_tipo(query)
    eff_numero = numero
    eff_anio = anio
    if (eff_numero is None or eff_anio is None) and query:
        m = _NUM_ANIO_RE.search(query)
        if m:
            eff_numero = eff_numero or m.group(1)
            eff_anio = eff_anio or int(m.group(2))

    if eff_tipo == "constitucion" and eff_anio:
        resolved = await get_norma(tipo="constitucion", anio=eff_anio)
        resolved["data"] = {"resuelto": True, **resolved["data"]}
        return resolved
    if eff_tipo and eff_numero and eff_anio:
        resolved = await get_norma(tipo=eff_tipo, anio=eff_anio, numero=eff_numero)
        resolved["data"] = {"resuelto": True, **resolved["data"]}
        return resolved

    # Degradado: devolver URLs canónicas de búsqueda + guía.
    q = quote_plus(query)
    data = {
        "status": "partial",
        "resuelto": False,
        "query": query,
        "mensaje": (
            "IMPO no ofrece una API JSON de búsqueda. Abrí estas URLs o, si "
            "conocés tipo/número/año, usá impo_get_norma para datos estructurados."
        ),
        "urls_busqueda": [
            {"nombre": "Búsqueda del sitio (WordPress)", "url": f"{BASE_URL}/?s={q}"},
            {
                "nombre": "Buscador de bases (CGI legacy)",
                "url": f"{BASE_URL}/cgi-bin/bases/principalBases.cgi?tipoServicio=3",
            },
        ],
        "sugerencia": (
            "Para obtener el texto de una norma usá impo_get_norma con "
            "tipo='ley'|'decreto'|'constitucion', numero y anio (año de 4 dígitos)."
        ),
    }
    return envelope(
        data,
        api=API_NAME,
        url=f"{BASE_URL}/?s={q}",
        cached=False,
        extra={"degraded": True},
    )
