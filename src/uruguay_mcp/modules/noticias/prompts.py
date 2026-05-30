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


@prompt(
    name="noticias_monitorear_tema",
    module=MODULE,
    description="Instrucción para monitorear la cobertura de un tema en las noticias de gobierno.",
)
def noticias_monitorear_tema(tema: str, subsite: str = DEFAULT_SUBSITE) -> str:
    return (
        f"Monitorea la cobertura del tema '{tema}' en las noticias de gobierno. "
        f"Primero buscá ocurrencias con noticias_buscar (parámetro query='{tema}') "
        "para obtener resultados del buscador de gub.uy. "
        f"Luego listá las noticias más recientes del subsitio '{subsite}' con "
        "noticias_recientes y filtrá manualmente las que mencionen el tema en "
        "título o resumen. Presentá un resumen de cobertura: cuántas noticias "
        "encontraste, las fechas más recientes y los titulares más relevantes. "
        "Aclaralo: noticias_buscar es parcial (no devuelve fechas ni categorías) "
        "y noticias_recientes extrae datos del HTML (sin el artículo completo)."
    )
