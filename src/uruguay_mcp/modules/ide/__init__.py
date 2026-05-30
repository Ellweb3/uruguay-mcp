"""IDE Uruguay module (datos espaciales: WFS + geocodificación AGESIC).

Importing this package registers its tools and module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="IDE Uruguay (Datos Espaciales)",
        description=(
            "Infraestructura de Datos Espaciales de Uruguay (AGESIC). Capas WFS "
            "del GeoServer vectorial (catastro, departamentos, calles, "
            "hidrografía) y API REST de geocodificación de direcciones "
            "(directa e inversa, EPSG:4326)."
        ),
    )
)

# Side-effect imports: register all @tool / @prompt / @resource handlers.
from . import prompts as prompts  # noqa: E402,F401
from . import resources as resources  # noqa: E402,F401
from . import tools as tools  # noqa: E402,F401
