"""Reusable MCP prompts for the DGI (Dirección General Impositiva) module.

Devuelven instrucciones listas para usar (en español) que orientan al modelo
hacia las herramientas reales del módulo (``dgi_buscar_valor``,
``dgi_listar_datos`` y ``dgi_tabla``).
"""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="dgi_valor_referencia",
    module=MODULE,
    description=(
        "Genera una instrucción para obtener un valor fiscal de referencia "
        "vigente de la DGI (Unidad Indexada, IPC, recargos por mora Art.94, "
        "coeficiente ITP)."
    ),
)
def dgi_valor_referencia(tema: str = "unidad indexada") -> str:
    return (
        f"Necesito el valor fiscal de referencia más reciente de '{tema}' de la "
        "DGI (Dirección General Impositiva). Paso 1: usá dgi_buscar_valor con "
        f"query='{tema}' para localizar el archivo correcto (elige el período "
        "más reciente) y traer una vista previa de la tabla. Si necesitás "
        "explorar el catálogo completo de valores (Unidad Indexada, IPC, "
        "cotizaciones, coeficiente ITP, tasas de recargos Art.94 o de "
        "facilidades Art.33), usá dgi_listar_datos (filtrando por tema). Paso 2: "
        "si la vista previa no alcanza, pasá la 'url' a dgi_tabla para leer la "
        "hoja completa. Reportá el título, el período (YYYY-MM) y los valores "
        "relevantes, aclarando de qué hoja salieron."
    )


@prompt(
    name="dgi_consultar_tabla",
    module=MODULE,
    description=(
        "Genera una instrucción para leer una planilla de valores de la DGI con "
        "dgi_tabla, recordando que vienen como .ods multi-hoja."
    ),
)
def dgi_consultar_tabla(url: str = "") -> str:
    destino = f"la planilla en {url}" if url else "una planilla de valores de la DGI"
    return (
        f"Leé {destino} con la herramienta dgi_tabla. Tené en cuenta que los "
        "archivos de la DGI suelen ser planillas .ods con VARIAS hojas y con "
        "filas de título y de relleno (no hay un encabezado fijo): dgi_tabla "
        "devuelve las filas crudas (listas de celdas) y n_hojas. Si la hoja 0 "
        "no tiene lo que buscás, volvé a llamar a dgi_tabla cambiando 'hoja'. "
        "Interpretá las filas para extraer el valor pedido e indicá la hoja y la "
        "fila de la que lo tomaste. Si no tenés la url, obtenela primero con "
        "dgi_buscar_valor o dgi_listar_datos."
    )
