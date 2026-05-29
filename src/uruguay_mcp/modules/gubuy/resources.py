"""MCP resources for the State APIs/services catalog (gub.uy showcases).

Importing this module registers the resources as a side effect.
"""

from __future__ import annotations

from ...shared.registry import resource
from .constants import API_RES_FORMAT, BASE_URL, MODULE


@resource(
    uri="uru://gubuy/guia-catalogo",
    name="Guía del catálogo de servicios y APIs del Estado (gub.uy)",
    description=(
        "Cómo usar las herramientas del módulo gubuy para explorar "
        "aplicaciones, servicios y APIs del Estado uruguayo."
    ),
    module=MODULE,
    mime_type="text/markdown",
)
def guia_catalogo() -> str:
    return (
        "# Catálogo de servicios y APIs del Estado (gub.uy)\n\n"
        "Las aplicaciones y servicios del Estado uruguayo se publican como "
        "*showcases* en la extensión ckanext-showcase de "
        f"{BASE_URL} (~58 servicios, la mayoría con URL en vivo).\n\n"
        "## Herramientas disponibles\n\n"
        "- `gubuy_list_servicios`: lista el catálogo completo y filtra por "
        "texto (`query`) o etiqueta (`tag`) del lado del cliente.\n"
        "- `gubuy_get_servicio`: detalle de un servicio por ID o slug "
        "(`id`).\n"
        "- `gubuy_servicio_datasets`: datasets del Catálogo Nacional que "
        "alimentan un servicio (`showcase_id`).\n"
        "- `gubuy_search_apis`: datasets con recursos consumibles por "
        f"API/JSON (`query`), filtrados por `res_format:{API_RES_FORMAT}`.\n\n"
        "## Flujo recomendado\n\n"
        "1. Buscá el servicio con `gubuy_list_servicios`.\n"
        "2. Obtené su detalle con `gubuy_get_servicio`.\n"
        "3. Si necesitás sus fuentes, usá `gubuy_servicio_datasets`.\n"
        "4. Para integrar datos por API, usá `gubuy_search_apis`.\n"
    )


@resource(
    uri="uru://gubuy/etiquetas-frecuentes",
    name="Etiquetas frecuentes del catálogo gub.uy",
    description=(
        "Etiquetas habituales para filtrar servicios del Estado con "
        "gubuy_list_servicios."
    ),
    module=MODULE,
    mime_type="text/markdown",
)
def etiquetas_frecuentes() -> str:
    return (
        "# Etiquetas frecuentes (gub.uy)\n\n"
        "Usá estas etiquetas en el parámetro `tag` de "
        "`gubuy_list_servicios` para acotar la búsqueda:\n\n"
        "- `transparencia`: portales de acceso a información pública.\n"
        "- `compras`: compras y contrataciones estatales.\n"
        "- `transporte`: movilidad y transporte público.\n"
        "- `salud`: servicios del sistema de salud.\n"
        "- `api`: servicios que exponen una API consumible.\n\n"
        "Las etiquetas se aplican del lado del cliente; combinalas con "
        "`query` para búsquedas de texto libre.\n"
    )
