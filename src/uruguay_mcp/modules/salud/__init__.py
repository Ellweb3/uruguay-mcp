"""Health (salud) module — CKAN-backed health data from the national portal.

Importing this package registers its tools, prompts, resources and module
metadata. All data comes from the national open-data portal
(catalogodatos.gub.uy); this module ships its own tiny CKAN client and does not
import from other modules.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Datos de salud (Uruguay)",
        description=(
            "Datos de salud del Estado uruguayo vía el Catálogo Nacional de Datos "
            "Abiertos (CKAN): descubrimiento por el grupo 'salud' (276 datasets de "
            "MSP, FNR, ASSE e intendencias), metadatos de datasets, ubicación de "
            "policlínicas, gasto en medicamentos del FNR y consulta de datos "
            "tabulares (datastore)."
        ),
    )
)

# Side-effect imports: register all @tool / @prompt / @resource handlers.
from . import prompts as prompts  # noqa: E402,F401
from . import resources as resources  # noqa: E402,F401
from . import tools as tools  # noqa: E402,F401
