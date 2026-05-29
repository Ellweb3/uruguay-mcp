"""Constants for the State APIs/services catalog (gub.uy).

The machine-readable "catalog of State services/APIs" is the ckanext-showcase
extension running on the same CKAN host as the open-data catalog
(catalogodatos.gub.uy): ~58 showcases describing government applications and
services, most pointing to a live URL. Read access is public/anonymous.

Note: there is NO dedicated apis.gub.uy / api.gub.uy / catalogo.gub.uy host
(those resolve to NXDOMAIN); do not attempt them at runtime.
"""

from __future__ import annotations

API_NAME = "catalogodatos.gub.uy/showcase"
BASE_URL = "https://catalogodatos.gub.uy"
ACTION_URL = f"{BASE_URL}/api/3/action"
MODULE = "gubuy"

# ckanext_showcase_list returns the full ~58-item list (no server-side paging),
# so list/tag/text filtering happens client-side.
MAX_LIMIT = 200
DEFAULT_LIMIT = 50

# package_search page sizes for the API/JSON convenience search.
MAX_ROWS = 100
DEFAULT_ROWS = 20

# CKAN facet/fq values are CASE-SENSITIVE: 'JSON' has ~2253 hits, 'json' has 0.
API_RES_FORMAT = "JSON"
