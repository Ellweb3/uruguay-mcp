"""Reusable prompts for the health (salud) module."""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="salud_buscar_datos",
    module=MODULE,
    description="Instrucción para buscar datasets de salud en el catálogo nacional.",
)
def salud_buscar_datos(tema: str, organizacion: str | None = None) -> str:
    extra = (
        f" Limitá la búsqueda a la organización '{organizacion}' (parámetro org)."
        if organizacion
        else ""
    )
    return (
        f"Buscá datos de salud sobre '{tema}' con la herramienta salud_buscar "
        "(parámetro q). Por defecto descubre por el grupo 'salud' (mucho más amplio "
        "que organization:msp), abarcando MSP, FNR, ASSE e intendencias."
        f"{extra} Para cada resultado relevante indicá título, organización y qué "
        "recursos tienen datastore activo. Para el detalle completo de un dataset "
        "usá salud_get_dataset con su id o slug."
    )


@prompt(
    name="salud_consultar_medicamentos",
    module=MODULE,
    description="Instrucción para consultar el gasto en tratamientos con medicamentos del FNR.",
)
def salud_consultar_medicamentos(prestacion: str | None = None, anio: int | None = None) -> str:
    filtro = (
        f" Filtrá por la prestación/tratamiento '{prestacion}' (parámetro q)."
        if prestacion
        else ""
    )
    año = f" Acotá al año {anio} (parámetro anio)." if anio else ""
    return (
        "Consultá el gasto por tratamientos con medicamentos del FNR con la "
        "herramienta salud_medicamentos."
        f"{filtro}{año} Recordá que NO existe un 'Formulario Terapéutico de "
        "Medicamentos' en este catálogo: estos datos son de gasto del Fondo "
        "Nacional de Recursos. Para agregar por Area_prestacion o Prestacion, usá "
        "el parámetro sql con una única sentencia SELECT."
    )


@prompt(
    name="salud_explorar_recurso",
    module=MODULE,
    description="Instrucción para explorar y consultar un recurso tabular de salud.",
)
def salud_explorar_recurso(resource_id: str, objetivo: str | None = None) -> str:
    meta = f" El objetivo es: {objetivo}." if objetivo else ""
    return (
        f"Consultá los registros del recurso '{resource_id}' con la herramienta "
        "salud_datastore_query (el recurso debe tener datastore activo; verificalo "
        "antes con salud_get_dataset). Primero mirá los campos disponibles "
        "(result.fields) antes de filtrar, ya que los nombres vienen en español y con "
        "mayúsculas. Para agregaciones usá el parámetro sql con una única sentencia "
        f"SELECT, citando el resource_id y las columnas entre comillas dobles.{meta}"
    )
