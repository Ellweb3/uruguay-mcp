"""State APIs/services catalog module (gub.uy showcases).

Importing this package registers its tools and module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Catálogo de APIs del Estado (gub.uy)",
        description=(
            "Catálogo de aplicaciones y servicios/APIs del Estado uruguayo basado "
            "en la extensión ckanext-showcase de catalogodatos.gub.uy (~58 "
            "servicios con URL en vivo), más búsqueda de datasets consumibles por "
            "API/JSON (res_format:JSON)."
        ),
    )
)

# Side-effect imports: register @tool, @prompt and @resource handlers.
from . import prompts, resources, tools  # noqa: E402,F401
