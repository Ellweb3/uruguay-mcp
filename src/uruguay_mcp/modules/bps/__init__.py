"""BPS 'Observatorio / BPS en Cifras' module.

Importing this package registers its tools and module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Banco de Previsión Social",
        description=(
            "Observatorio del BPS (tablero 'BPS en Cifras'): indicadores de "
            "seguridad social uruguaya (jubilaciones, pensiones de sobrevivencia, "
            "pensiones asistenciales, subsidios, recaudación, cotizantes). "
            "Backend JSON público; los datos suelen estar más actualizados que el "
            "espejo de datasets del BPS en el Catálogo Nacional."
        ),
    )
)

# Side-effect imports: register all @tool, @prompt and @resource handlers.
from . import prompts, resources, tools  # noqa: E402,F401
