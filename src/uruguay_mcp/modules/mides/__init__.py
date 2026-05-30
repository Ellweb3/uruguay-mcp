"""MIDES module: prestaciones, indicadores sociales y recursos sociales.

Importing this package registers its tools and module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Desarrollo Social (MIDES)",
        description=(
            "Datos del Ministerio de Desarrollo Social: ~1875 datasets en el "
            "catálogo nacional (CKAN) con indicadores y prestaciones sociales "
            "(Tarjeta Uruguay Social, AFAM-PE, Asistencia a la Vejez, ENDIS) "
            "como series mensuales, y la Guía Nacional de Recursos Sociales "
            "(programas/servicios) vía búsqueda sobre el portal."
        ),
    )
)

# Side-effect imports: register all @tool / @prompt / @resource handlers.
from . import prompts as prompts  # noqa: E402,F401
from . import resources as resources  # noqa: E402,F401
from . import tools as tools  # noqa: E402,F401
