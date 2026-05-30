"""Constants for IMPO — Centro de Información Oficial de Uruguay.

IMPO (impo.com.uy) publica la normativa nacional (leyes, decretos,
constitución) y el Diario Oficial. La única superficie de datos abiertos
confiable es agregar ``?json=true`` a una URL de norma, que devuelve un JSON
(``application/json; charset=ISO-8859-1``). El Diario Oficial es sólo PDF y no
existe una API JSON de búsqueda documentada: la búsqueda degrada con elegancia
a URLs canónicas. Sin autenticación ni clave de API.
"""

from __future__ import annotations

API_NAME = "impo.com.uy"
BASE_URL = "https://www.impo.com.uy"
MODULE = "impo"

# Respuestas de IMPO vienen en latin-1, NO en utf-8.
ENCODING = "iso-8859-1"

# Esquema JSON oficial de las bases de IMPO (archivo estático de referencia).
SCHEMA_URL = f"{BASE_URL}/resources/basesIMPO.json"

# tipo público -> slug de la base consolidada (texto actualizado).
TIPO_SLUGS = {
    "ley": "leyes",
    "decreto": "decretos",
    "constitucion": "constitucion",
}

# Sólo ley y decreto tienen base "-originales" (texto tal como se publicó).
TIPOS_CON_ORIGINAL = {"ley", "decreto"}

# Secciones del Diario Oficial (PDF). 'um' = último momento.
DIARIO_SECCIONES = ("indice", "documentos", "avisos", "um")

# Recorte de la cantidad de artículos devueltos para no inflar la respuesta.
MAX_ARTICULOS = 100

# --- Feeds RSS de WordPress (UTF-8, NO latin-1 como las bases ?json=true) ---
# Búsqueda full-text del sitio: /?s={query}&feed=rss2&paged={n} (10 ítems/página).
SEARCH_FEED_URL = f"{BASE_URL}/?s={{query}}&feed=rss2&paged={{paged}}"
# Feed de novedades/noticias editoriales del sitio.
NEWS_FEED_URL = f"{BASE_URL}/feed/"

# Namespace de Dublin Core usado por <dc:creator> en los feeds de WordPress.
DC_NS = "http://purl.org/dc/elements/1.1/"

# Recorte de la cantidad de ítems devueltos por los feeds RSS.
MAX_FEED_ITEMS = 10
