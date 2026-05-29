"""Readable MCP resources for the Intendencia de Montevideo module.

Reference documents (markdown) that complement the tools: how the transport
OAuth2 credentials work and an index of the key IM data surfaces/tools.
"""

from __future__ import annotations

from ...shared.registry import resource
from .constants import MODULE


@resource(
    uri="uru://montevideo/credenciales-transporte",
    name="Credenciales OAuth2 del transporte de Montevideo",
    description=(
        "Cómo se autentican las herramientas de transporte público de la "
        "Intendencia de Montevideo (OAuth2 client-credentials)."
    ),
    module=MODULE,
    mime_type="text/markdown",
)
def credenciales_transporte() -> str:
    return (
        "# Credenciales OAuth2 del transporte de Montevideo\n\n"
        "La API de transporte público (`api.montevideo.gub.uy/transportepublico`) "
        "está protegida con OAuth2 *client-credentials*. El token bearer se emite "
        "en un host de autenticación aparte (`mvdapi-auth.montevideo.gub.uy/token`).\n\n"
        "## Variables de entorno\n\n"
        "- `URUGUAY_MCP_MVD_CLIENT_ID`: client id del flujo client-credentials.\n"
        "- `URUGUAY_MCP_MVD_CLIENT_SECRET`: client secret correspondiente.\n\n"
        "Si faltan, las herramientas de transporte devuelven un error tipado "
        "`validation_error`.\n\n"
        "## Herramientas afectadas\n\n"
        "- `montevideo_bus_eta`: tiempo de arribo en una parada.\n"
        "- `montevideo_bus_positions`: posiciones en tiempo real.\n"
        "- `montevideo_buses_near`: buses cerca de un punto.\n"
        "- `montevideo_list_busstops`: paradas (id, calles, ubicación).\n"
        "- `montevideo_busstop_lines`: líneas que pasan por una parada.\n\n"
        "Las herramientas CKAN de datos abiertos NO requieren credenciales.\n"
    )


@resource(
    uri="uru://montevideo/indice-datasets",
    name="Índice de datos clave de la Intendencia de Montevideo",
    description=(
        "Mapa de las superficies de datos de IM (portal CKAN y transporte) y de "
        "las herramientas para consultarlas."
    ),
    module=MODULE,
    mime_type="text/markdown",
)
def indice_datasets() -> str:
    return (
        "# Índice de datos clave de la Intendencia de Montevideo\n\n"
        "Dos superficies en un solo módulo.\n\n"
        "## 1. Portal de Datos Abiertos (CKAN, sin auth)\n\n"
        "`ckan.montevideo.gub.uy` — ~155 datasets.\n\n"
        "- `montevideo_search_datasets`: buscar datasets (q, organización, "
        "grupo, tags).\n"
        "- `montevideo_get_dataset`: metadatos y recursos por id o slug.\n"
        "- `montevideo_list_organizations`: dependencias que publican datos.\n"
        "- `montevideo_list_groups`: categorías/grupos temáticos.\n"
        "- `montevideo_query_datastore`: registros tabulares (recursos con "
        "datastore activo).\n"
        "- `montevideo_multas_transito`: índice de multas de tránsito (SUCIVE), "
        "datos AGREGADOS por año.\n\n"
        "## 2. Transporte público (OAuth2)\n\n"
        "`api.montevideo.gub.uy/transportepublico` — requiere credenciales "
        "(ver recurso `uru://montevideo/credenciales-transporte`).\n\n"
        "- `montevideo_bus_eta`: próximos buses en una parada.\n"
        "- `montevideo_bus_positions`: posiciones en tiempo real.\n"
        "- `montevideo_buses_near`: buses dentro de un radio de un punto.\n"
        "- `montevideo_list_busstops`: paradas de ómnibus.\n"
        "- `montevideo_busstop_lines`: líneas por parada.\n"
    )
