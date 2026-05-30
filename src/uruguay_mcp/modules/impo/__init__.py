"""Módulo IMPO — Centro de Información Oficial de Uruguay.

Importar este paquete registra sus herramientas y metadatos de módulo.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="IMPO — Normativa nacional y Diario Oficial",
        description=(
            "Centro de Información Oficial (impo.com.uy): normativa nacional "
            "(leyes, decretos, constitución) vía el mecanismo ?json=true y "
            "Diario Oficial (PDF por sección). La búsqueda es parcial: IMPO no "
            "expone una API JSON de búsqueda, por lo que degrada a URLs canónicas."
        ),
    )
)

# Side-effect imports: register all @tool / @prompt / @resource handlers.
from . import prompts as prompts  # noqa: E402,F401
from . import resources as resources  # noqa: E402,F401
from . import tools as tools  # noqa: E402,F401
