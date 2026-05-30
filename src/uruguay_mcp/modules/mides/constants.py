"""Constants for the MIDES module (Ministerio de Desarrollo Social).

Two surfaces in one module:

1. CKAN Action API at catalogodatos.gub.uy — the national open-data portal.
   MIDES publishes ~1875 datasets (mostly 'indicador' packages with monthly
   social-benefit series: Tarjeta Uruguay Social/TUS, AFAM-PE, Asistencia a la
   Vejez, ENDIS, etc.). All MIDES tools force ``fq=organization:mides``.
2. Guía Nacional de Recursos Sociales at guiaderecursos.mides.gub.uy — an
   Innova/Oracle WebCenter JSP portal with NO JSON/REST API. We GET the search
   page (cmdaction=search) and scrape the resulting HTML for canonical resource
   links. The module stays self-contained (no cross-module imports).
"""

from __future__ import annotations

# --- CKAN open-data portal (public, no auth) -----------------------------
CKAN_API_NAME = "catalogodatos.gub.uy"
CKAN_ACTION_URL = "https://catalogodatos.gub.uy/api/3/action"
CKAN_ORG = "mides"

# --- Guía Nacional de Recursos Sociales (JSP portal, HTML scrape) ---------
GUIA_API_NAME = "guiaderecursos.mides.gub.uy"
GUIA_BASE_URL = "https://guiaderecursos.mides.gub.uy"
GUIA_SEARCH_URL = f"{GUIA_BASE_URL}/mides/guiarecurso/templates/inicio.jsp"

MODULE = "mides"

# Client-side caps so a single call never returns a huge payload.
DEFAULT_ROWS = 20
MAX_ROWS = 100
DEFAULT_SERIE_LIMIT = 100
MAX_SERIE_LIMIT = 1000
DEFAULT_RECURSOS_LIMIT = 10
MAX_RECURSOS_LIMIT = 50
