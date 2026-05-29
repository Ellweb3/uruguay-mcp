"""Constants for the in-process datastore module.

This module loads tabular data from any source (CSV URL, CKAN resource) into a
LOCAL SQLite database, then runs read-only SQL across the loaded tables. That
makes cross-API JOINs possible: pull a series from the BCU and a table from the
catalog, then join them locally with a single SELECT.
"""

from __future__ import annotations

MODULE = "datastore"
API_NAME = "datastore (local SQLite)"

# Where the SQLite database lives. ":memory:" is shared process-wide because we
# keep a single persistent connection open for the lifetime of the server.
DB_PATH = ":memory:"

# Hard cap on rows ingested per load, so a runaway download can't exhaust memory.
MAX_ROWS = 50_000

# CKAN datastore page size used when paging through datastore_search.
CKAN_PAGE = 1000

# Wall-clock limit (seconds) for any single SQL query.
SQL_TIMEOUT = 5.0

# Cap on rows returned by a single SELECT.
MAX_RESULT_ROWS = 1000

# Default CKAN portal used by datastore_load_ckan_resource.
DEFAULT_CKAN_BASE = "https://catalogodatos.gub.uy"
