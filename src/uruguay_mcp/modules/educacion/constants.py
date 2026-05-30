"""Constants for the ANEP education module.

Backed by the national open-data CKAN portal (catalogodatos.gub.uy), scoped to
the ANEP organization (slug ``anep``). ANEP (Administración Nacional de
Educación Pública) is Uruguay's public-education authority.

Only two datasets exist under org ``anep``:

- ``anep-centros-anep`` — a single RAR-packed Shapefile resource whose URL has
  404'd since 2021 (no datastore; metadata/URL only).
- ``anep-http-sig-anep-edu-uy-siganep-formatos`` ("Oferta educativa de la
  ANEP") — five XLSX resources, three with an active datastore queryable via
  ``datastore_search``.

The ANEP Geoportal (sig.anep.edu.uy ArcGIS) is NOT a usable API — it only
serves a Web Adaptor config page — so it is intentionally out of scope.
"""

from __future__ import annotations

API_NAME = "catalogodatos.gub.uy"
BASE_URL = "https://catalogodatos.gub.uy"
ACTION_URL = f"{BASE_URL}/api/3/action"
MODULE = "educacion"

# Organization slug this module is hard-pinned to. package_search WITHOUT this
# filter leaks other orgs (e.g. q=matricula returns a MIDES dataset).
ORG = "anep"

# Known dataset slugs under org ``anep``.
DATASET_CENTROS = "anep-centros-anep"
DATASET_OFERTA = "anep-http-sig-anep-edu-uy-siganep-formatos"

# Resource ids inside the "Oferta educativa de la ANEP" dataset that expose an
# active CKAN datastore (queryable). Keyed by subsistema (subsystem) shortcut.
DATASTORE_RESOURCES: dict[str, str] = {
    "ces": "72248932-8432-4b6e-90d4-b0c3455a0c23",  # DGES / Secundaria (3995 rows)
    "cfe": "20277d11-aae6-41dc-8a0a-f767f4ff1db2",  # CFE / Formación docente
    "789": "566e7734-dd69-4b41-b735-4f8930b54fa6",  # 7° 8° 9° rural (55 rows)
}
# Default resource for educacion_centros when no subsistema is given (the
# richest, most-populated datastore).
DEFAULT_RESOURCE = DATASTORE_RESOURCES["ces"]

# Caps so a single call never returns a megabyte blob.
MAX_ROWS = 100
DEFAULT_ROWS = 20
