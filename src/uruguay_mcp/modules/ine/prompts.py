"""Reusable MCP prompts for the INE statistical catalog module.

These prompts return ready-to-use instructions in Spanish that steer a model
toward the module's real tools (``ine_search_studies``, ``ine_get_study`` and
``ine_list_ckan_datasets``).
"""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="ine_buscar_estudios",
    module=MODULE,
    description=(
        "Genera una instrucción para buscar estudios/encuestas en el catálogo "
        "ANDA del INE (Inventario de Operaciones Estadísticas)."
    ),
)
def ine_buscar_estudios(tema: str = "hogares", desde: int | None = None) -> str:
    rango = f" publicados desde {desde}" if desde is not None else ""
    return (
        f"Buscá estudios y operaciones estadísticas sobre '{tema}'{rango} en el "
        "catálogo ANDA del INE con la herramienta ine_search_studies. Para cada "
        "resultado relevante reportá el idno (string URY-...-vNN), el título, el "
        "organismo responsable (authoring_entity) y los años (year_start/year_end). "
        "Recordá que el idno es lo que se necesita después para pedir el detalle "
        "del estudio."
    )


@prompt(
    name="ine_metadatos_estudio",
    module=MODULE,
    description=(
        "Genera una instrucción para obtener los metadatos completos de un "
        "estudio del INE a partir de su idno ANDA."
    ),
)
def ine_metadatos_estudio(idno: str = "URY-INE-ECH-2023-v01") -> str:
    return (
        f"Obtené los metadatos completos del estudio con idno '{idno}' usando la "
        "herramienta ine_get_study. Resumí el tipo de estudio, el organismo "
        "responsable, el período cubierto, el tipo de acceso a los datos "
        "(data_access_type) y los enlaces disponibles (cuestionario, informe "
        "técnico y descarga de microdatos). Si el idno no existe, sugerí buscarlo "
        "primero con ine_search_studies."
    )


@prompt(
    name="ine_datos_catalogo_nacional",
    module=MODULE,
    description=(
        "Genera una instrucción para encontrar datasets del INE en el Catálogo "
        "Nacional (CKAN) cuando se necesitan recursos tabulares descargables."
    ),
)
def ine_datos_catalogo_nacional(tema: str = "precios") -> str:
    return (
        f"Buscá datasets del INE sobre '{tema}' en el Catálogo Nacional de datos "
        "abiertos con la herramienta ine_list_ckan_datasets. Para cada dataset "
        "indicá el título, una breve descripción y los recursos descargables "
        "(nombre, formato y URL). Usá esta vía cuando se necesiten archivos "
        "tabulares (CSV/Excel) que no están en el catálogo ANDA."
    )
