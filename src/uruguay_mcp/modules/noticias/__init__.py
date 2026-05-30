"""Government news module (noticias) sourced from gub.uy.

Importing this package registers its tools and module metadata. gub.uy exposes
no machine-readable feed, so the module parses HTML listings and search results.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Noticias de Gobierno (gub.uy)",
        description=(
            "Noticias oficiales del Estado uruguayo publicadas en gub.uy. Listado "
            "de noticias recientes por organismo (presidencia, ministerios) y "
            "búsqueda por texto. gub.uy no expone RSS/Atom/JSON, por lo que los "
            "datos se extraen del HTML de los listados y del buscador del portal."
        ),
    )
)

# Side-effect imports: register all @tool / @prompt / @resource handlers.
from . import prompts as prompts  # noqa: E402,F401
from . import resources as resources  # noqa: E402,F401
from . import tools as tools  # noqa: E402,F401
