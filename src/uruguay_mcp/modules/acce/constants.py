"""Constants for ACCE (Agencia Reguladora de Compras Estatales).

Two surfaces in one module:

1. OCDS REST/RSS API (public, no auth) at comprasestatales.gub.uy — open
   contracting data published as OCDS 1.1 record/release packages plus an
   RSS 2.0 feed of the latest releases. Base is plain HTTP (the server is
   WildFly and HTTPS is not served reliably).
2. CKAN Action API at catalogodatos.gub.uy — the same national open-data
   portal the catalogodatos module wraps. ``acce_buscar`` is a thin
   convenience wrapper that forces ``fq=organization:acce``.
"""

from __future__ import annotations

# --- OCDS open-contracting API (public, plain HTTP) ----------------------
OCDS_API_NAME = "comprasestatales.gub.uy/ocds"
OCDS_BASE_URL = "http://www.comprasestatales.gub.uy/ocds"
RSS_URL = f"{OCDS_BASE_URL}/rss"
RECORD_URL = f"{OCDS_BASE_URL}/record"
RELEASE_URL = f"{OCDS_BASE_URL}/release"

# --- CKAN open-data portal (public, no auth) -----------------------------
CKAN_API_NAME = "catalogodatos.gub.uy"
CKAN_ACTION_URL = "https://catalogodatos.gub.uy/api/3/action"
CKAN_ORG = "acce"

MODULE = "acce"

# Client-side caps so a single call never returns a huge payload.
DEFAULT_FEED_LIMIT = 50
MAX_FEED_LIMIT = 200
DEFAULT_ROWS = 20
MAX_ROWS = 100
# Cap the number of items echoed back when slimming a tender/award release.
MAX_ITEMS = 25
