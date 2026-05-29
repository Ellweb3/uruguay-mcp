"""National open-data catalog module (catalogodatos.gub.uy).

Importing this package registers its tools and module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Catálogo Nacional de Datos Abiertos",
        description=(
            "Portal CKAN de AGESIC con ~2680 datasets de 72 organizaciones del "
            "Estado uruguayo. Búsqueda de datasets, metadatos, organizaciones, "
            "categorías y consulta de datos tabulares (datastore)."
        ),
    )
)

# Side-effect imports: register all @tool / @prompt / @resource handlers.
from . import prompts as prompts  # noqa: E402,F401
from . import resources as resources  # noqa: E402,F401
from . import tools as tools  # noqa: E402,F401
