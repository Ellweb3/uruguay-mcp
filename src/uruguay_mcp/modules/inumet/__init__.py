"""Módulo de INUMET — clima de Uruguay (estaciones, pronóstico y alertas).

Importar este paquete registra sus herramientas y metadatos de módulo.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="INUMET — Meteorología de Uruguay",
        description=(
            "Datos del Instituto Uruguayo de Meteorología: observaciones actuales "
            "de las estaciones meteorológicas automáticas (EMA), pronóstico oficial "
            "del tiempo (~4 días) y advertencias/alertas meteorológicas vigentes."
        ),
    )
)

# Side-effect imports: register all @tool / @prompt / @resource handlers.
from . import prompts as prompts  # noqa: E402,F401
from . import resources as resources  # noqa: E402,F401
from . import tools as tools  # noqa: E402,F401
