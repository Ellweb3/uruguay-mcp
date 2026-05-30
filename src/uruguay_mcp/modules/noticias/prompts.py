"""Reusable prompts for the government news (noticias) module."""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import DEFAULT_SUBSITE, MODULE


@prompt(
    name="noticias_ultimas",
    module=MODULE,
    description="Instrucción para mostrar las últimas noticias de un organismo de gobierno.",
)
def noticias_ultimas(subsite: str = DEFAULT_SUBSITE, limit: int = 10) -> str:
    return (
        f"Mostrá las últimas {limit} noticias del subsitio '{subsite}' de gub.uy "
        "usando la herramienta noticias_recientes (parámetros subsite y limit). "
        "Para cada noticia indicá título, categoría, fecha y URL, y un resumen "
        "breve. Aclaralo: gub.uy no publica RSS ni JSON, así que los datos se "
        "extraen del HTML del listado (no del artículo completo)."
    )


@prompt(
    name="noticias_buscar_tema",
    module=MODULE,
    description="Instrucción para buscar noticias de gobierno por tema.",
)
def noticias_buscar_tema(tema: str, subsite: str | None = None) -> str:
    extra = (
        f" Limitá la búsqueda al subsitio '{subsite}' (parámetro subsite)."
        if subsite
        else ""
    )
    return (
        f"Buscá noticias de gobierno sobre '{tema}' con la herramienta "
        "noticias_buscar (parámetro query)."
        f"{extra} Recordá que esta búsqueda es parcial (status='partial'): los "
        "resúmenes son fragmentos del buscador de gub.uy (no el texto del "
        "artículo) y no traen fecha ni categoría. Para el contexto reciente de un "
        "organismo, complementá con noticias_recientes."
    )
