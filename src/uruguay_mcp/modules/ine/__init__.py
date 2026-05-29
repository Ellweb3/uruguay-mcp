"""INE statistical catalog module (ANDA/NADA + CKAN fallback).

Importing this package registers its tools and module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Instituto Nacional de Estadística",
        description=(
            "Catálogo ANDA (software NADA) alojado por el INE: el Inventario de "
            "Operaciones Estadísticas del Sistema Estadístico Nacional (~389 "
            "estudios de INE, BCU, OSE, MGAP, INC y otros organismos). Búsqueda "
            "de estudios, metadatos DDI por idno, y fallback CKAN con datasets "
            "del INE en el Catálogo Nacional."
        ),
    )
)

# Side-effect imports: register all @tool, @prompt and @resource handlers.
from . import prompts, resources, tools  # noqa: E402,F401
