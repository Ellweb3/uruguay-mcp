"""Reusable prompts for the ANEP education module."""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="educacion_explorar_anep",
    module=MODULE,
    description="Instrucción para explorar los datasets educativos de ANEP.",
)
def educacion_explorar_anep(tema: str | None = None) -> str:
    extra = (
        f" Enfocá la búsqueda en '{tema}' (parámetro q)."
        if tema
        else ""
    )
    return (
        "Explorá los datos educativos abiertos de ANEP. Primero listá los "
        "datasets disponibles con la herramienta educacion_buscar (la búsqueda "
        "ya está fijada a la organización ANEP)."
        f"{extra} Para cada dataset relevante indicá título y cantidad de "
        "recursos. Luego, para ver el detalle y los recursos consultables, "
        "usá educacion_get_dataset con su slug o id. Recordá que solo existen "
        "dos datasets: 'anep-centros-anep' y la 'Oferta educativa de la ANEP'."
    )


@prompt(
    name="educacion_centros_por_departamento",
    module=MODULE,
    description="Instrucción para consultar centros educativos de ANEP por departamento.",
)
def educacion_centros_por_departamento(
    departamento: str = "MONTEVIDEO", subsistema: str | None = None
) -> str:
    sub = (
        f" Consultá el subsistema '{subsistema}'."
        if subsistema
        else " Por defecto se consulta Secundaria (DGES)."
    )
    return (
        f"Consultá los centros educativos de ANEP en el departamento "
        f"'{departamento}' con la herramienta educacion_centros (parámetro "
        "departamento, sensible a mayúsculas)."
        f"{sub} Si el subsistema elegido es Primaria (ceip) o UTU (cetp), la "
        "herramienta devolverá la URL de descarga del XLSX en lugar de filas, "
        "porque esos recursos no tienen datastore. Mostrá los campos "
        "disponibles y una muestra de centros con su nombre, dirección, "
        "teléfono y matrícula cuando exista."
    )
