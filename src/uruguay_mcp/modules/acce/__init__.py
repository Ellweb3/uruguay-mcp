"""ACCE module: compras estatales (OCDS) y datasets abiertos de ACCE.

Importing this package registers its tools and module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Compras Estatales (ACCE)",
        description=(
            "Datos de contrataciones públicas de la Agencia Reguladora de Compras "
            "Estatales (ACCE): feed OCDS 1.1 de compras recientes, detalle de "
            "llamados y adjudicaciones por release, y datasets abiertos de ACCE "
            "(RUPE, históricos) en el catálogo nacional."
        ),
    )
)

# Side-effect imports: register all @tool / @prompt / @resource handlers.
from . import prompts as prompts  # noqa: E402,F401
from . import resources as resources  # noqa: E402,F401
from . import tools as tools  # noqa: E402,F401
