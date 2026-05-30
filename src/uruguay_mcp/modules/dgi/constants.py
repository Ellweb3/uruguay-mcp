"""Constants for the DGI (Dirección General Impositiva) open-data module.

La DGI NO expone una API: sus datos abiertos son planillas descargables
(``.ods`` con valores fiscales de referencia) y boletines en ``.pdf``,
publicados como enlaces directos dentro de páginas HTML de su sitio Drupal en
``gub.uy``. Por eso este módulo NO usa ``http.get_json`` sino que descarga el
HTML de los listados (para extraer los enlaces a archivos) y los binarios
``.ods``/``.xlsx``/``.csv`` (que se parsean con la stdlib).

No hay consulta por contribuyente ni cálculo en vivo (RUT, IVA, IRPF,
declaraciones están detrás de ID Uruguay / certificado y quedan fuera de
alcance). El tipo de cambio diario tampoco vive acá (es el módulo ``bcu``):
``dgi`` son valores fiscales de REFERENCIA + estadísticas.
"""

from __future__ import annotations

API_NAME = "gub.uy"
BASE_URL = "https://www.gub.uy/direccion-general-impositiva"

MODULE = "dgi"

# Listado paginado de archivos de valores de referencia (?page=N, 0-based).
DATOS_PATH = "/datos-y-estadisticas/datos"
# Páginas de boletines/estadísticas (enlaces a PDFs).
BOLETIN_PATH = "/datos-y-estadisticas/estadisticas/boletin-estadistico"
GASTO_PATH = "/datos-y-estadisticas/estadisticas/gasto-tributario"

# Sólo se admiten descargas desde este host (validación de URL).
ALLOWED_HOST_PREFIX = "https://www.gub.uy/"

# Formatos de planilla soportados por el parser de tablas.
TABLE_EXTS = (".ods", ".xlsx", ".csv")

# Tope de páginas a recorrer en el listado de /datos (la 0 trae ~16, la 1 ~4,
# la 2 ya viene vacía). Se corta antes si una página no aporta archivos nuevos.
MAX_PAGES = 10

# Topes para que una sola llamada nunca devuelva un blob enorme.
MAX_ROWS = 200
DEFAULT_ROWS = 50
# Vista previa de filas en dgi_buscar_valor.
PREVIEW_ROWS = 20

# Al expandir table:number-(columns|rows)-repeated nunca expandir un único
# repeat más allá de este tope (los repeats de relleno valen cientos/miles).
MAX_REPEAT = 64
