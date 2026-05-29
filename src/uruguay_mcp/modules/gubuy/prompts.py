"""MCP prompts for the State APIs/services catalog (gub.uy showcases).

Importing this module registers the prompts as a side effect.
"""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="gubuy_buscar_servicios",
    module=MODULE,
    description=(
        "Genera una instrucción para buscar aplicaciones y servicios del "
        "Estado uruguayo en el catálogo gub.uy."
    ),
)
def gubuy_buscar_servicios(tema: str = "", etiqueta: str = "") -> str:
    filtros = []
    if tema:
        filtros.append(f"que traten sobre '{tema}'")
    if etiqueta:
        filtros.append(f"con la etiqueta '{etiqueta}'")
    detalle = (" " + ", ".join(filtros)) if filtros else ""
    return (
        "Buscá aplicaciones y servicios del Estado uruguayo en el catálogo "
        f"gub.uy{detalle} usando la herramienta 'gubuy_list_servicios' "
        "(parámetros 'query' y 'tag'). Para cada resultado relevante, indicá "
        "nombre, descripción breve y la URL en vivo. Si necesitás el detalle "
        "completo de uno, usá 'gubuy_get_servicio'."
    )


@prompt(
    name="gubuy_buscar_apis",
    module=MODULE,
    description=(
        "Genera una instrucción para encontrar datasets del Estado "
        "consumibles por API/JSON."
    ),
)
def gubuy_buscar_apis(tema: str = "") -> str:
    objeto = f"sobre '{tema}'" if tema else "del Estado uruguayo"
    return (
        f"Encontrá datasets {objeto} que expongan recursos consumibles por "
        "API/JSON usando la herramienta 'gubuy_search_apis' (parámetro "
        "'query'). Para cada dataset, listá título, organización responsable "
        "y la URL del recurso JSON. Aclará que la búsqueda filtra por "
        "res_format:JSON."
    )


@prompt(
    name="gubuy_fuentes_de_servicio",
    module=MODULE,
    description=(
        "Genera una instrucción para identificar los datasets que alimentan "
        "un servicio del Estado."
    ),
)
def gubuy_fuentes_de_servicio(servicio: str) -> str:
    return (
        f"Identificá las fuentes de datos del servicio '{servicio}' del "
        "Estado uruguayo. Primero resolvé su ID o slug con "
        "'gubuy_list_servicios' o 'gubuy_get_servicio', y luego usá "
        "'gubuy_servicio_datasets' (parámetro 'showcase_id') para listar los "
        "datasets del Catálogo Nacional que lo alimentan. Si no hay datasets "
        "vinculados, indicálo explícitamente."
    )
