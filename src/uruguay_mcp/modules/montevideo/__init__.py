"""Intendencia de Montevideo module (open data + public transport).

Importing this package registers its tools and module metadata. Combines the
CKAN open-data portal (public reads) with the OAuth2-secured public-transport
REST API (real-time bus positions and arrival estimates).
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Intendencia de Montevideo",
        description=(
            "Datos de la Intendencia de Montevideo: portal CKAN de datos abiertos "
            "(~155 datasets, búsqueda, metadatos, organizaciones, categorías y "
            "datastore) y API de transporte público (posiciones de buses en tiempo "
            "real, tiempos de arribo, paradas y líneas). El transporte requiere "
            "credenciales OAuth2 (URUGUAY_MCP_MVD_CLIENT_ID / URUGUAY_MCP_MVD_CLIENT_SECRET)."
        ),
    )
)

# Side-effect imports: register @tool handlers, prompts and resources.
from . import prompts, resources, tools  # noqa: E402,F401
