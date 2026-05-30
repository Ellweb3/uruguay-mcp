"""Constants for the BPS 'Observatorio / BPS en Cifras' dashboard backend.

The Banco de Previsión Social (BPS) publishes its 'BPS en Cifras' dashboard on
top of a public, no-auth JSON REST backend (the ``DashboardNegocioWebRest``
service). All data endpoints are ``POST`` + JSON and return
Elasticsearch-shaped responses: an array of hits each like
``{"_index": ..., "_source": {...}}`` — the real payload lives under
``_source`` (the Angular app does ``t.map(x => x._source)``).

This data (jubilaciones, pensiones, recaudación, cotizantes, ...) is generally
fresher than the BPS dataset mirror in the MIDES / Catálogo Nacional.
"""

from __future__ import annotations

API_NAME = "observatorio.bps.gub.uy"
BASE_URL = "https://observatorio.bps.gub.uy/DashboardNegocioWebRest/api/wsDashboardWeb"

MODULE = "bps"

# Cap the rows returned for a single indicator so a call never returns a huge blob.
MAX_ROWS = 200
DEFAULT_ROWS = 50

# Cap how many bloques the client-side discovery crawl will fetch.
MAX_DISCOVERY = 40
