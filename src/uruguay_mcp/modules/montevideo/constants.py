"""Constants for the Intendencia de Montevideo data sources.

Two surfaces in one module:

1. CKAN Action API (public reads, no auth) at ckan.montevideo.gub.uy — the
   open-data portal (~155 datasets, CKAN 2.9.9). Identical to catalogodatos.
2. Public-transport REST API at api.montevideo.gub.uy, secured with OAuth2
   client-credentials. The bearer token is minted at a separate auth host
   (mvdapi-auth.montevideo.gub.uy). Credentials come from the environment.
"""

from __future__ import annotations

import os

# --- CKAN open-data portal (public) -------------------------------------
CKAN_API_NAME = "ckan.montevideo.gub.uy"
CKAN_BASE_URL = "https://ckan.montevideo.gub.uy"
ACTION_URL = f"{CKAN_BASE_URL}/api/3/action"

# --- Public transport API (OAuth2) --------------------------------------
TRANSPORT_API_NAME = "api.montevideo.gub.uy/transportepublico"
TRANSPORT_BASE_URL = "https://api.montevideo.gub.uy/api/transportepublico"
TOKEN_URL = "https://mvdapi-auth.montevideo.gub.uy/token"

MODULE = "montevideo"

# Cap CKAN page sizes so a single call never returns a megabyte blob.
MAX_ROWS = 100
DEFAULT_ROWS = 20

# Aggregate traffic-fine (SUCIVE) open dataset published by IM. This is
# statistical data (counts by ordinance, vehicle type, origin, year) — NOT a
# per-vehicle debt lookup (that lives behind a reCAPTCHA on sucive.gub.uy).
MULTAS_DATASET_SLUG = "multas-de-transito"

# Transport listing caps (client-side, the API itself is unbounded).
MAX_BUS_RESULTS = 200


def client_id() -> str | None:
    """OAuth2 client id, from ``URUGUAY_MCP_MVD_CLIENT_ID`` (None if unset)."""
    return os.environ.get("URUGUAY_MCP_MVD_CLIENT_ID") or None


def client_secret() -> str | None:
    """OAuth2 client secret, from ``URUGUAY_MCP_MVD_CLIENT_SECRET`` (None if unset)."""
    return os.environ.get("URUGUAY_MCP_MVD_CLIENT_SECRET") or None
