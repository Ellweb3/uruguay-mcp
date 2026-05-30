"""Constants for INUMET (Instituto Uruguayo de Meteorología).

Three surfaces, all on www.inumet.gub.uy (Drupal 10, sin autenticación):

1. EMA — observaciones de estaciones meteorológicas automáticas (JSON real,
   el ``.mch`` que consume la SPA de datos 24h). Sin parámetros.
2. Pronóstico — página HTML server-rendered (no existe API JSON); se scrapea.
3. Alertas/advertencias — página HTML server-rendered (no existe API JSON).

El sitio está detrás de Cloudflare; el JSON se cachea ``max-age=300`` (5 min).
"""

from __future__ import annotations

API_NAME = "inumet.gub.uy"
BASE_URL = "https://www.inumet.gub.uy"

# Estaciones meteorológicas automáticas (EMA): JSON real (~358KB) que consume
# la SPA /reportes/pages/datos24hv2/. Sin parámetros.
EMA_URL = f"{BASE_URL}/reportes/estadoActual/datos_inumet_ui_publica.mch"

# Páginas HTML (Drupal) — se scrapean, no hay API JSON.
PRONOSTICO_URL = f"{BASE_URL}/tiempo/pronostico"
ALERTA_URL = f"{BASE_URL}/alerta"

MODULE = "inumet"

# Topes de filas del lado del cliente para no devolver bloques enormes.
MAX_ESTACIONES = 120
MAX_DIAS_PRONOSTICO = 7

# Mapa id-de-variable -> clave útil en la salida slim de estaciones.
# observaciones[] está alineado por POSICIÓN a variables[]; estos ids permiten
# localizar cada variable sin depender del orden del arreglo.
VAR_TEMP_AIRE = 47  # TempAire (C)
VAR_HUM_RELATIVA = 25  # HumRelativa (%)
VAR_INT_VIENTO = 29  # IntViento (nudos)
VAR_DIR_VIENTO = 8  # DirViento (grados)
VAR_INT_RAFAGA = 28  # IntRafaga (nudos)
VAR_PRES_MAR = 45  # PresAtmMar (hPa)
VAR_PRECIP_HORARIA = 94  # precipHoraria (mm)
VAR_VISIBILIDAD = 74  # Visibilidad (km)

# Factor de conversión nudos -> km/h (los vientos del EMA vienen en NUDOS).
NUDOS_A_KMH = 1.852
