"""Discoverable tools for IDE Uruguay (WFS geo features + AGESIC geocoding)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from ...shared import errors
from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import (
    CRS_URN,
    DEFAULT_COUNT,
    GEO_API_NAME,
    GEO_CANDIDATES_URL,
    GEO_DIRECUNICA_URL,
    GEO_REVERSE_URL,
    LAYER_PARCELARIO_RURAL,
    LAYER_PARCELARIO_URBANO,
    MODULE,
    SRS_NAME,
    WFS_API_NAME,
)
from .schemas import (
    FeaturesArgs,
    GeocodificarArgs,
    GeocodificarInversoArgs,
    ListarCapasArgs,
    ParcelaCatastralArgs,
)

# WFS GetCapabilities uses the WFS 2.0 namespace for <FeatureType>/<Name>/<Title>.
_WFS_NS = {"wfs": "http://www.opengis.net/wfs/2.0"}


# --- WFS capabilities parsing --------------------------------------------
def _parse_capas(xml_text: str, filtro: str | None, incluir_titulos: bool) -> list[dict[str, Any]]:
    """Project the capabilities <FeatureType> entries to a slim layer list."""
    root = ET.fromstring(xml_text)
    capas: list[dict[str, Any]] = []
    for ft in root.iter("{http://www.opengis.net/wfs/2.0}FeatureType"):
        name = (ft.findtext("wfs:Name", namespaces=_WFS_NS) or "").strip()
        if not name:
            continue
        workspace = name.split(":", 1)[0] if ":" in name else ""
        layer = name.split(":", 1)[1] if ":" in name else name
        if filtro and filtro.lower() not in name.lower():
            continue
        entry: dict[str, Any] = {
            "workspace": workspace,
            "layer": layer,
            "typeNames": name,
        }
        if incluir_titulos:
            entry["title"] = (ft.findtext("wfs:Title", namespaces=_WFS_NS) or "").strip() or None
        capas.append(entry)
    return capas


# --- GeoJSON slimming -----------------------------------------------------
def _iter_coords(coords: Any):
    """Yield (lon, lat) pairs from arbitrarily nested GeoJSON coordinates."""
    if (
        isinstance(coords, list)
        and len(coords) >= 2
        and isinstance(coords[0], int | float)
        and isinstance(coords[1], int | float)
    ):
        yield coords[0], coords[1]
        return
    if isinstance(coords, list):
        for sub in coords:
            yield from _iter_coords(sub)


def _geom_summary(geometry: dict[str, Any] | None) -> dict[str, Any] | None:
    """Compute bbox + centroid for a geometry without echoing the full coords."""
    if not geometry:
        return None
    gtype = geometry.get("type")
    pts = list(_iter_coords(geometry.get("coordinates", [])))
    if not pts:
        return {"type": gtype}
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return {
        "type": gtype,
        "bbox": [min(lons), min(lats), max(lons), max(lats)],
        "centroid": [sum(lons) / len(lons), sum(lats) / len(lats)],
        "num_coords": len(pts),
    }


def _slim_feature(feature: dict[str, Any], slim: bool) -> dict[str, Any]:
    geometry = feature.get("geometry")
    out: dict[str, Any] = {
        "id": feature.get("id"),
        "properties": feature.get("properties", {}),
    }
    if slim:
        out["geometry"] = _geom_summary(geometry)
    else:
        out["geometry"] = geometry
    return out


def _slim_collection(fc: dict[str, Any], slim: bool) -> dict[str, Any]:
    features = fc.get("features", []) if isinstance(fc, dict) else []
    return {
        "numberMatched": fc.get("numberMatched"),
        "numberReturned": fc.get("numberReturned"),
        "totalFeatures": fc.get("totalFeatures"),
        "features": [_slim_feature(f, slim) for f in features],
    }


def _build_getfeature_params(
    capa: str,
    bbox: str | None,
    cql_filter: str | None,
    count: int,
    propiedades: str | None,
    solo_conteo: bool,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "typeNames": capa,
        "outputFormat": "application/json",
        "srsName": SRS_NAME,
    }
    if solo_conteo:
        params["resultType"] = "hits"
    else:
        params["count"] = count
    if bbox:
        # Append the CRS URI so axis order (miny,minx,maxy,maxx) is unambiguous.
        params["bbox"] = f"{bbox},{CRS_URN}"
    if cql_filter:
        params["CQL_FILTER"] = cql_filter
    if propiedades:
        params["propertyName"] = propiedades
    return params


# --- Geocoding normalization ---------------------------------------------
def _slim_geo_item(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize a flat v1 geocoding result to the essential fields."""
    return {
        "type": item.get("type"),
        "address": item.get("address"),
        "lat": item.get("lat"),
        "lng": item.get("lng"),
        "nomVia": item.get("nomVia"),
        "portalNumber": item.get("portalNumber"),
        "departamento": item.get("departamento"),
        "localidad": item.get("localidad"),
        "postalCode": item.get("postalCode"),
    }


def _geo_results(payload: Any) -> list[dict[str, Any]]:
    items = payload if isinstance(payload, list) else []
    return [_slim_geo_item(it) for it in items if isinstance(it, dict)]


# --- Tools ----------------------------------------------------------------
@tool(
    name="ide_listar_capas",
    module=MODULE,
    summary=(
        "Listar las capas WFS disponibles en el GeoServer vectorial de la IDE "
        "Uruguay (mapas.ide.uy). Devuelve nombre, workspace y typeNames; usar "
        "antes de ide_features para encontrar la capa correcta."
    ),
    params_model=ListarCapasArgs,
    keywords=[
        "wfs",
        "capas",
        "layers",
        "getcapabilities",
        "geoserver",
        "listar",
        "catalogo",
        "ide",
    ],
)
async def listar_capas(
    filtro: str | None = None, incluir_titulos: bool = False
) -> dict[str, Any]:
    xml_text, cached, url = await client.get_capabilities()
    capas = _parse_capas(xml_text, filtro, incluir_titulos)
    return envelope(
        {"count": len(capas), "capas": capas},
        api=WFS_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="ide_features",
    module=MODULE,
    summary=(
        "Consulta WFS GetFeature genérica contra el GeoServer vectorial de la "
        "IDE Uruguay, devolviendo GeoJSON recortado. Requiere una capa "
        "(typeNames) y, para capas grandes, un bbox o un cql_filter."
    ),
    params_model=FeaturesArgs,
    keywords=[
        "wfs",
        "getfeature",
        "geojson",
        "features",
        "bbox",
        "cql",
        "geo",
        "capa",
        "ide",
    ],
)
async def features(
    capa: str,
    bbox: str | None = None,
    cql_filter: str | None = None,
    count: int = DEFAULT_COUNT,
    propiedades: str | None = None,
    slim: bool = True,
    solo_conteo: bool = False,
) -> dict[str, Any]:
    params = _build_getfeature_params(
        capa, bbox, cql_filter, count, propiedades, solo_conteo
    )
    result, cached, url = await client.get_feature(params)
    if solo_conteo:
        data = {
            "numberMatched": (result or {}).get("numberMatched"),
            "typeNames": capa,
        }
    else:
        data = _slim_collection(result or {}, slim)
    return envelope(data, api=WFS_API_NAME, url=url, cached=cached)


@tool(
    name="ide_parcela_catastral",
    module=MODULE,
    summary=(
        "Parcelas catastrales (parcelario urbano/rural de la DNC) por bbox o por "
        "departamento+padrón. Devuelve GeoJSON recortado con padron, depto, "
        "localidad, manzana y área. La capa urbana tiene ~1M parcelas: requiere "
        "bbox o filtro."
    ),
    params_model=ParcelaCatastralArgs,
    keywords=[
        "catastro",
        "parcela",
        "cadastre",
        "padron",
        "parcelario",
        "manzana",
        "predio",
        "ide",
    ],
)
async def parcela_catastral(
    tipo: str = "urbano",
    bbox: str | None = None,
    departamento: str | None = None,
    padron: int | None = None,
    cql_filter: str | None = None,
    count: int = DEFAULT_COUNT,
    slim: bool = True,
) -> dict[str, Any]:
    capa = LAYER_PARCELARIO_RURAL if tipo == "rural" else LAYER_PARCELARIO_URBANO

    clauses: list[str] = []
    if departamento:
        clauses.append(f"depto='{departamento.upper()}'")
    if padron is not None:
        clauses.append(f"padron={padron}")
    if cql_filter:
        clauses.append(f"({cql_filter})")
    combined = " AND ".join(clauses) or None

    if not bbox and not combined:
        raise errors.ValidationError(
            "La capa catastral es enorme: indique un bbox o un filtro "
            "(departamento y/o padron, o cql_filter)."
        )

    params = _build_getfeature_params(capa, bbox, combined, count, None, False)
    result, cached, url = await client.get_feature(params)
    return envelope(
        _slim_collection(result or {}, slim),
        api=WFS_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="ide_geocodificar",
    module=MODULE,
    summary=(
        "Geocodificar una dirección uruguaya a coordenadas (EPSG:4326) usando la "
        "API REST de direcciones de AGESIC (direcUnica; /candidates para "
        "autocompletado). Devuelve calle, número, departamento, localidad y "
        "código postal."
    ),
    params_model=GeocodificarArgs,
    keywords=[
        "geocodificar",
        "geocode",
        "direccion",
        "address",
        "coordenadas",
        "direcciones",
        "agesic",
        "ide",
    ],
)
async def geocodificar(
    direccion: str, limite: int = 5, autocompletar: bool = False
) -> dict[str, Any]:
    endpoint = GEO_CANDIDATES_URL if autocompletar else GEO_DIRECUNICA_URL
    payload, cached, url = await client.geocode(
        endpoint, {"q": direccion, "limit": limite}
    )
    results = _geo_results(payload)
    return envelope(
        {"count": len(results), "results": results},
        api=GEO_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="ide_geocodificar_inverso",
    module=MODULE,
    summary=(
        "Geocodificación inversa: de lat/lon (EPSG:4326) a las direcciones "
        "oficiales más cercanas usando la API REST de AGESIC (reverse). Devuelve "
        "calle, número de puerta, departamento, localidad y código postal."
    ),
    params_model=GeocodificarInversoArgs,
    keywords=[
        "reverse",
        "inverso",
        "geocode",
        "coordenadas",
        "direccion",
        "geocodificacion",
        "ide",
    ],
)
async def geocodificar_inverso(
    latitud: float, longitud: float, limite: int = 3
) -> dict[str, Any]:
    payload, cached, url = await client.geocode(
        GEO_REVERSE_URL,
        {"latitud": latitud, "longitud": longitud, "limit": limite},
    )
    results = _geo_results(payload)
    return envelope(
        {"count": len(results), "results": results},
        api=GEO_API_NAME,
        url=url,
        cached=cached,
    )
