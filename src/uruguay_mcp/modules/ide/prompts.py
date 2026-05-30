"""Reusable prompts for the IDE Uruguay (datos espaciales) module."""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="ide_buscar_capa_y_features",
    module=MODULE,
    description="Instrucción para descubrir una capa WFS y consultar sus features.",
)
def ide_buscar_capa_y_features(tema: str, bbox: str | None = None) -> str:
    extra = (
        f" Acotá la consulta al área bbox '{bbox}' (formato "
        "miny,minx,maxy,maxx en EPSG:4326)."
        if bbox
        else " Acordate de pasar un bbox o un cql_filter para capas grandes."
    )
    return (
        f"Para datos espaciales sobre '{tema}', primero listá las capas WFS "
        "disponibles con ide_listar_capas (parámetro filtro). Elegí el "
        "typeNames adecuado y luego consultá los datos con ide_features "
        f"(parámetro capa).{extra} Por defecto la geometría viene recortada "
        "(tipo, bbox y centroide); pedí slim=false solo si necesitás las "
        "coordenadas completas."
    )


@prompt(
    name="ide_consultar_catastro",
    module=MODULE,
    description="Instrucción para consultar parcelas catastrales por departamento y padrón.",
)
def ide_consultar_catastro(
    departamento: str, padron: str | None = None
) -> str:
    extra = (
        f" Filtrá por el padrón {padron}."
        if padron
        else " Si no indicás un padrón, acotá con un bbox para no traer toda la capa."
    )
    return (
        f"Consultá las parcelas catastrales del departamento '{departamento}' "
        "con la herramienta ide_parcela_catastral (parámetro departamento en "
        f"mayúsculas).{extra} Indicá tipo='urbano' o 'rural' según corresponda. "
        "Mostrá padron, localidad, manzana y área de cada parcela."
    )


@prompt(
    name="ide_geocodificar_direccion",
    module=MODULE,
    description="Instrucción para geocodificar una dirección uruguaya.",
)
def ide_geocodificar_direccion(direccion: str) -> str:
    return (
        f"Geocodificá la dirección '{direccion}' con la herramienta "
        "ide_geocodificar. Incluí el TIPO de vía (AVENIDA, CALLE, RUTA) para "
        "mejorar el acierto. Devolvé las coordenadas lat/lng (EPSG:4326), el "
        "departamento, la localidad y el código postal. Para el camino inverso "
        "(de coordenadas a dirección) usá ide_geocodificar_inverso."
    )
