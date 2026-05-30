"""Constants for government news (noticias) on gub.uy.

gub.uy is a Drupal site with RSS/Atom and JSON:API DISABLED. There is no
machine-readable feed, so this module parses the HTML listing pages
(/{subsite}/comunicacion/noticias) and the Drupal Search API results
(/buscar?search_api_fulltext=...) with stdlib/regex.

Two listing layouts exist across subsites:
- presidencia: ``Box-title``/``Box-subtitle`` cards, date "29 de Mayo, 2026".
- ministries:  ``Media-title``/``Media-subtitle`` cards, date "29/05/2026".
"""

from __future__ import annotations

API_NAME = "gub.uy"
BASE_URL = "https://www.gub.uy"

MODULE = "noticias"

# Default subsite (the presidency news listing).
DEFAULT_SUBSITE = "presidencia"

# Listing/search path templates (joined to BASE_URL).
LISTING_PATH = "/{subsite}/comunicacion/noticias"
SEARCH_PATH = "/buscar"
SEARCH_SUBSITE_PATH = "/{subsite}/buscar"

# The Drupal Search API form field (NOT the default 'keys').
SEARCH_FIELD = "search_api_fulltext"

# Only results whose URL contains this path are real news articles.
NEWS_URL_MARKER = "/comunicacion/noticias/"

# Each listing page renders ~10 cards; loop pages to honour a larger limit.
CARDS_PER_PAGE = 10

# Client-side caps so a single call never returns a huge payload.
DEFAULT_LIMIT = 10
MAX_LIMIT = 50
DEFAULT_SEARCH_LIMIT = 20
MAX_SEARCH_LIMIT = 50
# Hard cap on how many listing pages a single noticias_recientes call may fetch.
MAX_PAGES = 6
