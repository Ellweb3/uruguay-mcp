"""Constants for the IDE Uruguay (Infraestructura de Datos Espaciales).

Two public, no-auth surfaces in one module:

1. OGC WFS 2.0.0 served by GeoServer at mapas.ide.uy. The REAL working OGC
   endpoint is ``/geoserver-vectorial/wfs`` (the documented ``/geoservicios/*``
   facade only answers GetCapabilities). It advertises ~507 FeatureTypes across
   ~33 workspaces (cadastre, departamentos, calles, hidrografía, ...). Features
   come back as standard GeoJSON FeatureCollections.
2. AGESIC address/geocoding REST API at direcciones.ide.uy (Spring Boot /
   Swagger). Plain JSON arrays (NOT GeoJSON): forward, autocomplete and reverse
   geocoding with lat/lng in EPSG:4326.

The module is self-contained: no cross-module imports.
"""

from __future__ import annotations

# --- WFS (GeoServer vectorial) -------------------------------------------
WFS_API_NAME = "mapas.ide.uy/wfs"
WFS_URL = "https://mapas.ide.uy/geoserver-vectorial/wfs"
WFS_VERSION = "2.0.0"
# WFS 2.0 with EPSG:4326 defaults to lat,lon axis order; appending the CRS URI
# to the bbox keeps the order unambiguous (miny,minx,maxy,maxx).
CRS_URN = "urn:ogc:def:crs:EPSG::4326"
SRS_NAME = "EPSG:4326"

# Cadastre layers (huge: ~1M urban parcels) — always require bbox or CQL filter.
LAYER_PARCELARIO_URBANO = "ET_CATASTRO:parcelario_urbano"
LAYER_PARCELARIO_RURAL = "ET_CATASTRO:parcelario_rural"

# --- AGESIC geocoding REST API (direcciones.ide.uy) ----------------------
GEO_API_NAME = "direcciones.ide.uy"
GEO_BASE_URL = "https://direcciones.ide.uy"
GEO_V1 = f"{GEO_BASE_URL}/api/v1/geocode"
GEO_DIRECUNICA_URL = f"{GEO_V1}/direcUnica"
GEO_CANDIDATES_URL = f"{GEO_V1}/candidates"
GEO_REVERSE_URL = f"{GEO_V1}/reverse"

MODULE = "ide"

# Client-side caps so a single WFS call never returns a multi-megabyte blob.
DEFAULT_COUNT = 50
MAX_COUNT = 200
DEFAULT_LIMIT = 5
MAX_LIMIT = 25
