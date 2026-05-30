"""Herramientas descubribles para INUMET (clima de Uruguay).

Tres herramientas:

- ``inumet_estaciones``: observaciones actuales de estaciones automáticas (EMA),
  parseando la matriz estaciones/variables/fechas/observaciones del JSON.
- ``inumet_pronostico``: pronóstico oficial (~4 días), scrapeando la página HTML.
- ``inumet_alertas``: advertencias meteorológicas vigentes, scrapeando /alerta.

Las dos últimas degradan a ``status='partial'`` si el HTML cambia y no se puede
parsear, en lugar de inventar datos.
"""

from __future__ import annotations

import re
from typing import Any

from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import (
    API_NAME,
    BASE_URL,
    MAX_DIAS_PRONOSTICO,
    MODULE,
    NUDOS_A_KMH,
    VAR_DIR_VIENTO,
    VAR_HUM_RELATIVA,
    VAR_INT_RAFAGA,
    VAR_INT_VIENTO,
    VAR_PRECIP_HORARIA,
    VAR_PRES_MAR,
    VAR_TEMP_AIRE,
    VAR_VISIBILIDAD,
)
from .schemas import AlertasArgs, EstacionesArgs, PronosticoArgs

# --- EMA: parseo de la matriz de observaciones ---------------------------


def _latest_by_variable(payload: dict[str, Any]) -> dict[int, dict[int, tuple[int, Any]]]:
    """Mapear id-de-variable -> {stationIndex: (fechaIndex, valor)} más reciente.

    ``observaciones[]`` está alineado por POSICIÓN a ``variables[]``. ``datos`` es
    una matriz [stationIndex][fechaIndex]; se recorre hacia atrás para hallar el
    último valor no nulo por estación.
    """
    variables = payload.get("variables") or []
    observaciones = payload.get("observaciones") or []
    out: dict[int, dict[int, tuple[int, Any]]] = {}
    for var_pos, var in enumerate(variables):
        var_id = var.get("id")
        if var_id is None or var_pos >= len(observaciones):
            continue
        obs = observaciones[var_pos] or {}
        i_fechas = obs.get("iFechas") or []
        datos = obs.get("datos") or []
        per_station: dict[int, tuple[int, Any]] = {}
        for st_idx, serie in enumerate(datos):
            if not serie:
                continue
            for pos in range(len(serie) - 1, -1, -1):
                val = serie[pos]
                if val is not None:
                    fecha_idx = i_fechas[pos] if pos < len(i_fechas) else pos
                    per_station[st_idx] = (fecha_idx, val)
                    break
        out[var_id] = per_station
    return out


def _kt_to_kmh(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value) * NUDOS_A_KMH, 1)
    except (TypeError, ValueError):
        return None


def _matches(est: dict[str, Any], needle: str) -> bool:
    needle = needle.lower()
    for key in ("displayNamePublic", "nombre", "idStr"):
        if needle in str(est.get(key) or "").lower():
            return True
    return needle == str(est.get("id") or "").lower()


def _slim_station(
    st_idx: int,
    est: dict[str, Any],
    latest: dict[int, dict[int, tuple[int, Any]]],
    fechas: list[str],
) -> dict[str, Any]:
    def value(var_id: int) -> Any:
        hit = latest.get(var_id, {}).get(st_idx)
        return hit[1] if hit else None

    def timestamp() -> str | None:
        # Usar la fecha del dato de temperatura; si falta, la del viento.
        for var_id in (VAR_TEMP_AIRE, VAR_INT_VIENTO):
            hit = latest.get(var_id, {}).get(st_idx)
            if hit and hit[0] < len(fechas):
                return fechas[hit[0]]
        return None

    viento_kt = value(VAR_INT_VIENTO)
    rafaga_kt = value(VAR_INT_RAFAGA)
    return {
        "id": est.get("id"),
        "idStr": est.get("idStr"),
        "nombre": est.get("displayNamePublic") or est.get("nombre"),
        "lat": est.get("latitud"),
        "lon": est.get("longitud"),
        "altitud": est.get("altitud"),
        "gerencia": est.get("gerencia"),
        "temp_c": value(VAR_TEMP_AIRE),
        "hum_pct": value(VAR_HUM_RELATIVA),
        "viento_kt": viento_kt,
        "viento_kmh": _kt_to_kmh(viento_kt),
        "dir_viento_grados": value(VAR_DIR_VIENTO),
        "rafaga_kt": rafaga_kt,
        "rafaga_kmh": _kt_to_kmh(rafaga_kt),
        "presion_hpa": value(VAR_PRES_MAR),
        "precip_mm": value(VAR_PRECIP_HORARIA),
        "visibilidad_km": value(VAR_VISIBILIDAD),
        "timestamp": timestamp(),
    }


@tool(
    name="inumet_estaciones",
    module=MODULE,
    summary=(
        "Observaciones actuales de las estaciones meteorológicas automáticas "
        "(EMA) de INUMET en todo Uruguay: temperatura, humedad, viento, presión, "
        "precipitación y visibilidad por estación."
    ),
    params_model=EstacionesArgs,
    keywords=[
        "inumet",
        "estaciones",
        "ema",
        "weather station",
        "temperatura",
        "viento",
        "humedad",
        "uruguay",
        "observaciones",
        "clima",
    ],
)
async def estaciones(
    station: str | None = None,
    automatic_only: bool = True,
    limit: int = 120,
) -> dict[str, Any]:
    payload, cached, url = await client.fetch_ema()
    estaciones_raw = payload.get("estaciones") or []
    fechas = payload.get("fechas") or []
    latest = _latest_by_variable(payload)

    rows: list[dict[str, Any]] = []
    for st_idx, est in enumerate(estaciones_raw):
        if automatic_only and not est.get("tipoAutomatica"):
            continue
        if station and not _matches(est, station):
            continue
        rows.append(_slim_station(st_idx, est, latest, fechas))
        if len(rows) >= limit:
            break

    return envelope(
        {"count": len(rows), "estaciones": rows},
        api=API_NAME,
        url=url,
        cached=cached,
    )


# --- Pronóstico: scraping del HTML de Drupal ------------------------------

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_ITEM_RE = re.compile(
    r'<div[^>]*class="[^"]*pronostico-item[^"]*"[^>]*>(.*?)(?=<div[^>]*class="[^"]*'
    r'pronostico-item|</section|</main|\Z)',
    re.IGNORECASE | re.DOTALL,
)
_DESC_RE = re.compile(
    r'<div[^>]*class="[^"]*pronostico-desc[^"]*"[^>]*>(.*?)</div>',
    re.IGNORECASE | re.DOTALL,
)
_DIA_RE = re.compile(
    r"\b(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s+\d{1,2}",
    re.IGNORECASE,
)
_MINMAX_RE = re.compile(
    r"m[ií]n\.?\s*(-?\d+)\s*[º°]?\s*c?.*?m[aá]x\.?\s*(-?\d+)",
    re.IGNORECASE | re.DOTALL,
)
_VIENTO_RE = re.compile(r"viento\s*:?\s*([^<\n.]+)", re.IGNORECASE)
_PERIODO_RE = re.compile(r"(ma[ñn]ana|tarde\s*/?\s*noche|tarde|noche|madrugada)", re.IGNORECASE)


def _strip_tags(html: str) -> str:
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", html)).strip()


def _parse_dia(block: str) -> dict[str, Any] | None:
    text = _strip_tags(block)
    dia_m = _DIA_RE.search(text)
    if not dia_m:
        return None
    minmax = _MINMAX_RE.search(text)
    temp_min = int(minmax.group(1)) if minmax else None
    temp_max = int(minmax.group(2)) if minmax else None

    periodos: list[dict[str, Any]] = []
    descs = _DESC_RE.findall(block)
    for raw in descs:
        desc_text = _strip_tags(raw)
        if not desc_text:
            continue
        per_m = _PERIODO_RE.search(desc_text)
        viento_m = _VIENTO_RE.search(desc_text)
        periodos.append(
            {
                "periodo": per_m.group(1).strip() if per_m else None,
                "descripcion": desc_text,
                "viento": viento_m.group(1).strip() if viento_m else None,
            }
        )
    return {
        "dia": dia_m.group(0).strip(),
        "temp_min_c": temp_min,
        "temp_max_c": temp_max,
        "periodos": periodos,
    }


@tool(
    name="inumet_pronostico",
    module=MODULE,
    summary=(
        "Pronóstico oficial del tiempo de INUMET para Uruguay (~4 días). Scrapea "
        "la página /tiempo/pronostico (no existe API JSON) y devuelve días con "
        "temperatura mínima/máxima y descripción por período."
    ),
    params_model=PronosticoArgs,
    keywords=[
        "inumet",
        "pronostico",
        "forecast",
        "tiempo",
        "uruguay",
        "clima",
        "temperatura",
        "weather forecast",
    ],
)
async def pronostico(days: int = MAX_DIAS_PRONOSTICO) -> dict[str, Any]:
    html, cached, url = await client.fetch_pronostico()
    dias: list[dict[str, Any]] = []
    for block in _ITEM_RE.findall(html):
        parsed = _parse_dia(block)
        if parsed:
            dias.append(parsed)
        if len(dias) >= days:
            break

    status = "ok" if dias else "partial"
    extra = {"status": status}
    nota = None
    if not dias:
        nota = (
            "No se pudieron extraer días del pronóstico; la estructura HTML de "
            "INUMET pudo cambiar. Consultá la página oficial."
        )
    return envelope(
        {"status": status, "count": len(dias), "dias": dias, "nota": nota},
        api=API_NAME,
        url=url,
        cached=cached,
        extra=extra,
    )


# --- Alertas: scraping del HTML de /alerta --------------------------------

_MAIN_RE = re.compile(r"<main[^>]*>(.*?)</main>", re.IGNORECASE | re.DOTALL)
_NO_ALERTA_RE = re.compile(r"no\s+hay\s+advertencia", re.IGNORECASE)
_NIVEL_RE = re.compile(r"\b(amarill[ao]|naranja|roj[ao])\b", re.IGNORECASE)
_PDF_RE = re.compile(r'href="([^"]+\.pdf)"', re.IGNORECASE)


@tool(
    name="inumet_alertas",
    module=MODULE,
    summary=(
        "Advertencias meteorológicas vigentes en Uruguay (alertas de INUMET). "
        "Scrapea la página /alerta (no existe API JSON) e indica si hay alerta "
        "activa, su nivel (amarilla/naranja/roja) y el texto/PDF si está presente."
    ),
    params_model=AlertasArgs,
    keywords=[
        "inumet",
        "alerta",
        "alertas",
        "advertencia",
        "warning",
        "aviso",
        "uruguay",
        "amarilla",
        "naranja",
        "roja",
    ],
)
async def alertas() -> dict[str, Any]:
    html, cached, url = await client.fetch_alerta()
    main_m = _MAIN_RE.search(html)
    region = main_m.group(1) if main_m else html
    texto = _strip_tags(region)

    if not texto:
        data = {
            "status": "partial",
            "activa": None,
            "mensaje": (
                "No se pudo leer la región principal de /alerta; la estructura "
                "HTML pudo cambiar."
            ),
            "nivel": None,
            "detalle": None,
            "pdf_url": None,
            "fuente_url": url,
        }
        return envelope(data, api=API_NAME, url=url, cached=cached, extra={"status": "partial"})

    if _NO_ALERTA_RE.search(texto):
        data = {
            "status": "ok",
            "activa": False,
            "mensaje": "No hay advertencia meteorológica vigente.",
            "nivel": None,
            "detalle": None,
            "pdf_url": None,
            "fuente_url": url,
        }
        return envelope(data, api=API_NAME, url=url, cached=cached, extra={"status": "ok"})

    nivel_m = _NIVEL_RE.search(texto)
    pdf_m = _PDF_RE.search(region)
    pdf_url = pdf_m.group(1) if pdf_m else None
    if pdf_url and pdf_url.startswith("/"):
        pdf_url = f"{BASE_URL}{pdf_url}"
    data = {
        "status": "ok",
        "activa": True,
        "mensaje": texto[:600],
        "nivel": nivel_m.group(1).lower() if nivel_m else None,
        "detalle": texto,
        "pdf_url": pdf_url,
        "fuente_url": url,
    }
    return envelope(data, api=API_NAME, url=url, cached=cached, extra={"status": "ok"})
