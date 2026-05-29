"""Cross-source local datastore module.

Loads tabular data from any source (CSV URL, CKAN resource) into a local SQLite
database and runs read-only SQL across the loaded tables — enabling cross-API
JOINs. Importing this package registers its tools, prompts, resources and
module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Datastore local (SQL cruzado entre fuentes)",
        description=(
            "Carga datos tabulares de cualquier fuente (CSV o recurso CKAN) en una "
            "base SQLite local y permite consultarlos con SQL de sólo lectura. "
            "Habilita JOINs entre datos de distintas APIs (BCU, INE, catálogo, etc.)."
        ),
    )
)

# Side-effect imports: register @tool, @prompt and @resource handlers.
from . import prompts, resources, tools  # noqa: E402,F401
