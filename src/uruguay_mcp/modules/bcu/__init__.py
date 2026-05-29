"""Banco Central del Uruguay exchange-rate module (cotizaciones.bcu.gub.uy).

Importing this package registers its tools and module metadata.
"""

from __future__ import annotations

from ...shared.registry import ModuleInfo, registry
from .constants import MODULE

registry.register_module(
    ModuleInfo(
        name=MODULE,
        title="Banco Central del Uruguay (cotizaciones)",
        description=(
            "Servicios SOAP públicos del BCU con las cotizaciones (tipo de cambio "
            "compra y venta) de divisas y unidades indexadas. Listado de monedas, "
            "fecha del último cierre y cotizaciones por rango de fechas, con atajo "
            "para el dólar."
        ),
    )
)

# Side-effect imports: register all @tool, @prompt and @resource handlers.
from . import prompts as prompts  # noqa: E402
from . import resources as resources  # noqa: E402
from . import tools as tools  # noqa: E402
