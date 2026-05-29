"""Constants for the national open-data catalog (catalogodatos.gub.uy).

A standard CKAN 2.x portal run by AGESIC: ~2680 datasets across 72 publishing
organizations and 22 topic groups. All access is via the public CKAN Action
API (no key required for reads).
"""

from __future__ import annotations

API_NAME = "catalogodatos.gub.uy"
BASE_URL = "https://catalogodatos.gub.uy"
ACTION_URL = f"{BASE_URL}/api/3/action"
MODULE = "catalogodatos"

# Cap CKAN page sizes so a single call never returns a megabyte blob.
MAX_ROWS = 100
DEFAULT_ROWS = 20
