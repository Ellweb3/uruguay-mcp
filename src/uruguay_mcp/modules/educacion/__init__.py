"""ANEP education module (datos abiertos de educación pública).

Backed by the national open-data CKAN portal (catalogodatos.gub.uy), scoped to
the ANEP organization. Importing this package registers its tools, prompts,
resources and module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Educación pública (ANEP)",
        description=(
            "Datos abiertos de ANEP (Administración Nacional de Educación "
            "Pública) publicados en el Catálogo Nacional (CKAN). Búsqueda de "
            "datasets, metadatos y consulta de centros educativos (oferta, "
            "matrícula, departamento) vía datastore."
        ),
    )
)

# Side-effect imports: register all @tool / @prompt / @resource handlers.
from . import prompts as prompts  # noqa: E402,F401
from . import resources as resources  # noqa: E402,F401
from . import tools as tools  # noqa: E402,F401
