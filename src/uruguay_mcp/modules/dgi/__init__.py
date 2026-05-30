"""DGI (Dirección General Impositiva) open-data module.

Importing this package registers its tools and module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Dirección General Impositiva",
        description=(
            "Valores fiscales de referencia y estadísticas de la DGI "
            "(Dirección General Impositiva): Unidad Indexada, IPC, cotizaciones, "
            "coeficientes ITP/activo fijo, tasas de recargos por mora (Art.94) y "
            "de facilidades (Art.33), y boletines estadísticos. La DGI no expone "
            "API: son planillas .ods/.xlsx/.csv y boletines .pdf descargados de "
            "su sitio en gub.uy. No incluye consulta por contribuyente ni "
            "cálculo en vivo (RUT/IVA/IRPF están autenticados)."
        ),
    )
)

# Side-effect imports: register all @tool, @prompt and @resource handlers.
from . import prompts, resources, tools  # noqa: E402,F401
