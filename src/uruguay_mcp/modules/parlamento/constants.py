"""Constants for the Parlamento del Uruguay module.

Two surfaces in one module:

1. CKAN Action API (public reads, no key) at catalogodatos.gub.uy, pre-scoped to
   the organization ``parlamento-uruguayo`` (display "Parlamento del Uruguay",
   ~23 datasets, license odc-uy). Datasets cover asistencias, actividades,
   pedidos de informes, leyes, comisiones, etc. Resources are split per
   legislatura; only ``datastore_active`` resources can be queried row by row.
2. Direct JSON endpoints on parlamento.gub.uy — the underlying source the CKAN
   resources point at. These return a bare JSON ARRAY (no CKAN envelope) with a
   different, per-legislator shape for asistencias.
"""

from __future__ import annotations

# --- CKAN open-data portal (public, org-scoped) -------------------------
CKAN_API_NAME = "catalogodatos.gub.uy"
CKAN_BASE_URL = "https://catalogodatos.gub.uy"
ACTION_URL = f"{CKAN_BASE_URL}/api/3/action"

# Always inject this org filter so the module only ever sees Parlamento data.
ORG_SLUG = "parlamento-uruguayo"

# --- Direct parlamento.gub.uy JSON endpoints (raw arrays) ---------------
DIRECT_API_NAME = "parlamento.gub.uy"
DIRECT_BASE_URL = "https://parlamento.gub.uy"
ASISTENCIA_URL = (
    f"{DIRECT_BASE_URL}/camarasycomisiones/representantes/transparencia/"
    "datos-abiertos/asistencia-a-sesiones/json"
)
ACTIVIDAD_URL = f"{DIRECT_BASE_URL}/documentosyleyes/datos-abiertos/actividad/json"

MODULE = "parlamento"

# Cap page sizes so a single call never returns a megabyte blob.
MAX_ROWS = 100
DEFAULT_ROWS = 20
