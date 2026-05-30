"""Reusable prompts for the Parlamento del Uruguay module."""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="parlamento_buscar_datos",
    module=MODULE,
    description="Instrucción para buscar datasets del Parlamento por tema.",
)
def parlamento_buscar_datos(tema: str) -> str:
    return (
        f"Buscá datasets del Parlamento del Uruguay sobre '{tema}' con la "
        "herramienta parlamento_buscar (parámetro query). Para cada resultado "
        "relevante indicá título, cantidad de recursos y cuáles tienen "
        "datastore activo. Si necesitás el detalle completo y los resource_id "
        "por legislatura, usá parlamento_get_dataset con el slug o uuid."
    )


@prompt(
    name="parlamento_asistencias_legislatura",
    module=MODULE,
    description="Instrucción para consultar asistencias por cámara y legislatura.",
)
def parlamento_asistencias_legislatura(
    camara: str = "representantes", legislatura: str = ""
) -> str:
    leg = (
        f" de la legislatura {legislatura}"
        if legislatura
        else " (usando la legislatura más reciente disponible)"
    )
    return (
        f"Consultá las asistencias a sesiones de la cámara '{camara}'{leg} con la "
        "herramienta parlamento_asistencias. Recordá que la copia del Catálogo "
        "Nacional expone filas a nivel sesión (Fecha, Asunto, Carpetas), no el "
        "presentismo individual por legislador. Mostrá los campos disponibles, "
        "el total de registros y una muestra de filas."
    )


@prompt(
    name="parlamento_actividades_agenda",
    module=MODULE,
    description="Instrucción para revisar actividades/citaciones de una cámara.",
)
def parlamento_actividades_agenda(camara: str = "senado") -> str:
    return (
        f"Revisá las actividades y citaciones de la cámara '{camara}' con la "
        "herramienta parlamento_actividades (plenarios y comisiones). Si querés "
        "filtrar por una comisión o tema, pasá un texto en el parámetro query. "
        "Resumí las próximas o más recientes actividades indicando fecha, "
        "comisión y sala."
    )
