"""Parlamento del Uruguay module (org-scoped over catalogodatos.gub.uy).

Importing this package registers its tools and module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Parlamento del Uruguay",
        description=(
            "Datos abiertos del Poder Legislativo (Cámara de Representantes y "
            "Senado) publicados en el Catálogo Nacional bajo la organización "
            "'parlamento-uruguayo': asistencias, actividades/citaciones, pedidos "
            "de informes, leyes, comisiones y proyectos."
        ),
    )
)

# Side-effect imports: register all @tool / @prompt / @resource handlers.
from . import prompts as prompts  # noqa: E402,F401
from . import resources as resources  # noqa: E402,F401
from . import tools as tools  # noqa: E402,F401
