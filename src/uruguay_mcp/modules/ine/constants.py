"""Constants for the INE statistical catalog (ANDA / NADA + CKAN fallback).

Primary source is the ANDA (software NADA) catalog hosted by the Instituto
Nacional de Estadística at www4.ine.gub.uy. It is the cross-agency
'Inventario de Operaciones Estadísticas del Sistema Estadístico Nacional',
so many studies belong to BCU, OSE, MGAP, INC, etc., not only INE.

Only the public read endpoints ``catalog/search`` and ``catalog/{idno}`` are
open (no auth). NADA admin/collections endpoints require an API key and are
not exposed here.

A thin CKAN fallback (organization=ine on catalogodatos.gub.uy) supplements
ANDA with ~15 tabular/downloadable datasets.
"""

from __future__ import annotations

API_NAME = "ine.gub.uy"
ANDA_BASE_URL = "https://www4.ine.gub.uy/Anda5/index.php/api"
ANDA_SEARCH_URL = f"{ANDA_BASE_URL}/catalog/search"
ANDA_CATALOG_URL = f"{ANDA_BASE_URL}/catalog"

CKAN_API_NAME = "catalogodatos.gub.uy"
CKAN_ACTION_URL = "https://catalogodatos.gub.uy/api/3/action"
CKAN_ORG_SLUG = "ine"

MODULE = "ine"

# Cap ANDA / CKAN page sizes so a single call never returns a huge blob.
MAX_ROWS = 100
DEFAULT_ROWS = 20

# Cap CKAN DataStore row fetches so a single query never returns a huge blob.
MAX_DATASTORE_ROWS = 100
DEFAULT_DATASTORE_ROWS = 20
