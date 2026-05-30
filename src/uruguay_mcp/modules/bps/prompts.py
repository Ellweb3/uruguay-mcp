"""Reusable MCP prompts for the BPS (Observatorio / BPS en Cifras) module.

These prompts return ready-to-use instructions in Spanish that steer a model
toward the module's real tools (``bps_buscar_indicador``, ``bps_indicador`` and
``bps_serie_csv``).
"""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="bps_pasividades_actuales",
    module=MODULE,
    description=(
        "Genera una instrucción para obtener cifras vigentes de pasividades del "
        "BPS (jubilaciones, pensiones) desde el Observatorio."
    ),
)
def bps_pasividades_actuales(tema: str = "jubilaciones") -> str:
    return (
        f"Necesito las cifras más actuales de '{tema}' del Observatorio del BPS "
        "(BPS en Cifras). Paso 1: usá bps_buscar_indicador con query='" + tema + "' "
        "para localizar el indicador relevante y anotá su bloque y pagina. Paso 2: "
        "usá bps_indicador con ese bloque (y pagina) para traer la serie; reportá "
        "el nombre del indicador, las columnas, el total de filas y los valores "
        "principales (p.ej. el Total). Indicá también la fecha de actualización "
        "(fechaUpload de archivosSeries) si está disponible."
    )


@prompt(
    name="bps_consultar_indicador",
    module=MODULE,
    description=(
        "Genera una instrucción para consultar un indicador del BPS por su bloque "
        "y, si se necesita, descargar sus series CSV crudas."
    ),
)
def bps_consultar_indicador(bloque: int = 2) -> str:
    return (
        f"Consultá el indicador del Observatorio del BPS en el bloque {bloque} con "
        "la herramienta bps_indicador. Resumí el nombre, la descripción, las "
        "columnas (columnas) y una muestra de los datos (datos), incluyendo el "
        "número de filas (n_filas). Si necesitás los datos crudos completos, usá "
        "bps_serie_csv con el id_pagina que devuelve bps_indicador para descargar "
        "los archivos CSV de esa página. Si el bloque no existe, el campo "
        "encontrado será False: en ese caso buscá el indicador con "
        "bps_buscar_indicador."
    )
