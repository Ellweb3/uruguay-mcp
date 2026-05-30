"""Recursos de referencia para el módulo IMPO."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import BASE_URL, MODULE, SCHEMA_URL


@resource(
    uri="uru://impo/guia-de-uso",
    name="Guía de uso de IMPO (normativa y Diario Oficial)",
    description="Cómo acceder a la normativa nacional y al Diario Oficial de IMPO.",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_de_uso() -> str:
    return (
        "# Guía de uso de IMPO\n\n"
        f"Centro de Información Oficial ({BASE_URL}): normativa nacional "
        "(leyes, decretos, constitución) y Diario Oficial.\n\n"
        "## Herramientas\n\n"
        "1. **`impo_get_norma`** — obtené una norma como JSON estructurado por "
        "`tipo` ('ley'|'decreto'|'constitucion'), `numero` y `anio` (4 dígitos). "
        "Usá `version='original'` para el texto tal como se publicó (sólo "
        "ley/decreto).\n"
        "2. **`impo_diario_oficial`** — enlaces PDF del Diario Oficial por sección "
        "(`indice`, `documentos`, `avisos`, `um`) para una fecha (por defecto hoy).\n"
        "3. **`impo_buscar_normativa`** — búsqueda best-effort (DEGRADADA): "
        "resuelve a la norma si hay tipo/número/año, o devuelve URLs de búsqueda.\n\n"
        "## Patrones de URL (mecanismo `?json=true`)\n\n"
        "- Ley consolidada: `/bases/leyes/{numero}-{anio}?json=true` "
        "(ej. `18331-2008`).\n"
        "- Ley original: `/bases/leyes-originales/{numero}-{anio}?json=true`.\n"
        "- Decreto: `/bases/decretos/{numero}-{anio}?json=true` "
        "(¡año de 4 dígitos! `500-1991`, no `500-91`).\n"
        "- Constitución: `/bases/constitucion/{anio}-{anio}?json=true` "
        "(ej. `1967-1967`, sin número).\n\n"
        "## Notas y advertencias\n\n"
        "- **Codificación**: las respuestas vienen en `ISO-8859-1` (latin-1), no "
        "utf-8. El módulo ya las decodifica correctamente.\n"
        "- **Diario Oficial**: sólo PDF, sin API JSON. URLs "
        "`/diariooficial/{YYYY}/{MM}/{DD}/{seccion}.pdf` (mes y día con cero).\n"
        "- **Sin búsqueda JSON**: la única búsqueda del sitio es WordPress "
        "`/?s=...` (HTML). La búsqueda es parcial por diseño.\n"
        "- Algunos campos (`notasArticulo`, `titulosArticulo`) traen HTML "
        "embebido; el módulo lo limpia. Las URLs relativas se prefijan con el host.\n"
    )


@resource(
    uri="uru://impo/esquema",
    name="Esquema JSON de las bases de IMPO",
    description="Descripción del esquema de respuesta de las bases de IMPO (basesIMPO.json).",
    module=MODULE,
    mime_type="text/markdown",
)
def esquema() -> str:
    return (
        "# Esquema JSON de las bases de IMPO\n\n"
        f"IMPO publica el esquema oficial (JSON Schema draft-07) en {SCHEMA_URL}.\n\n"
        "## Campos principales de una norma\n\n"
        "- `tipoNorma`, `nroNorma`, `anioNorma`, `secNorma`: identificación.\n"
        "- `nombreNorma`: título/denominación de la norma.\n"
        "- `leyenda`: 'Documento Actualizado' (consolidada) o 'Documento "
        "original'.\n"
        "- `fechaPromulgacion`, `fechaPublicacion`: fechas clave.\n"
        "- `urlVerImagen`, `urlVerOriginal`: rutas (relativas) a la imagen del "
        "Diario Oficial.\n"
        "- `RNLD` (tomo/semestre/anio/pagina): referencia al Registro Nacional de "
        "Leyes y Decretos.\n"
        "- `vistos`, `firmantes`: encabezado y firmas.\n"
        "- `articulos[]`: lista de artículos con `nroArticulo`, `secArticulo`, "
        "`tituloArticulo`, `textoArticulo` (texto plano), `urlArticulo` y "
        "`notasArticulo` (puede traer HTML embebido).\n\n"
        "## Mecanismo de acceso\n\n"
        "Agregá `?json=true` a la URL de una norma para obtener este JSON en lugar "
        "del HTML. Decodificá los bytes como `ISO-8859-1`. Usá `impo_get_norma` "
        "para no tener que construir las URLs a mano.\n"
    )
