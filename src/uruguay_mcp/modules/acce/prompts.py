"""Reusable prompts for the ACCE (compras estatales) module."""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="acce_compras_recientes",
    module=MODULE,
    description="Instrucción para explorar las compras estatales más recientes (OCDS).",
)
def acce_compras_recientes(tag: str | None = None) -> str:
    extra = (
        f" Filtrá por el tipo de evento '{tag}' (parámetro tag)."
        if tag
        else ""
    )
    return (
        "Mostrá las contrataciones públicas más recientes de Uruguay con la "
        "herramienta acce_recientes (feed OCDS de ACCE)."
        f"{extra} Para cada evento indicá id_compra, tipo (tag), título y fecha. "
        "Si una compra es de interés, usá acce_get_compra con su id_compra para "
        "ver todas sus etapas y luego acce_get_release con cada release_id para "
        "el detalle del llamado o la adjudicación."
    )


@prompt(
    name="acce_analizar_compra",
    module=MODULE,
    description="Instrucción para analizar una compra estatal por su id_compra.",
)
def acce_analizar_compra(idcompra: str) -> str:
    return (
        f"Analizá la compra estatal '{idcompra}'. Primero obtené sus etapas con "
        "acce_get_compra (id_compra) para listar los eventos (release_id y tag). "
        "Luego, para los eventos relevantes, llamá a acce_get_release con cada "
        "release_id: en los llamados (tender) resumí organismo comprador, objeto, "
        "método e ítems; en las adjudicaciones (award) resumí proveedor "
        "adjudicatario, ítems y valor si está publicado (suele faltar)."
    )


@prompt(
    name="acce_buscar_datasets",
    module=MODULE,
    description="Instrucción para buscar datasets abiertos publicados por ACCE.",
)
def acce_buscar_datasets(tema: str = "") -> str:
    objetivo = f"sobre '{tema}' " if tema else ""
    return (
        f"Buscá datasets {objetivo}publicados por ACCE en el Catálogo Nacional de "
        "Datos Abiertos con la herramienta acce_buscar (parámetro query). Estos "
        "incluyen el RUPE (Registro Único de Proveedores del Estado) y datos "
        "históricos de compras. Indicá título, descripción y recursos disponibles "
        "de cada dataset relevante."
    )
