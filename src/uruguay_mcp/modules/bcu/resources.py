"""MCP resources for the BCU module (cotizaciones del Banco Central del Uruguay).

Importing this file registers the resources as a side effect.
"""

from __future__ import annotations

from ...shared.registry import resource
from .constants import MODULE


@resource(
    uri="uru://bcu/codigos-moneda",
    name="Tabla de códigos de moneda del BCU",
    description="Códigos numéricos de las monedas más usadas en las cotizaciones del BCU.",
    module=MODULE,
    mime_type="text/markdown",
)
def codigos_moneda() -> str:
    return (
        "# Códigos de moneda del BCU\n\n"
        "Códigos numéricos usados por las herramientas de cotizaciones "
        "('bcu_cotizaciones', 'bcu_cotizacion_usd'). Para el listado completo y "
        "actualizado usá la herramienta 'bcu_listar_monedas'.\n\n"
        "| Código | Moneda |\n"
        "| --- | --- |\n"
        "| 2225 | DLS. USA BILLETE (dólar estadounidense) |\n"
        "| 1001 | REAL BILLETE (real brasileño) |\n"
        "| 0501 | EURO |\n"
        "| 0502 | PESO ARGENTINO |\n"
        "| 0\\* | Unidades indexadas locales (UI, UR, UP) — grupo 0 |\n"
    )


@resource(
    uri="uru://bcu/grupos-moneda",
    name="Nota sobre grupos de moneda del BCU",
    description="Explica los grupos de moneda (divisas vs. unidades locales) del BCU.",
    module=MODULE,
    mime_type="text/markdown",
)
def grupos_moneda() -> str:
    return (
        "# Grupos de moneda del BCU\n\n"
        "Las herramientas del BCU aceptan un parámetro 'grupo' que filtra el "
        "tipo de moneda:\n\n"
        "- **Grupo 2 — Divisas (por defecto):** monedas y billetes extranjeros "
        "(USD, BRL, EUR, ARS, ...). Es el grupo más usado.\n"
        "- **Grupo 0 — Unidades locales:** unidades indexadas nacionales "
        "(UI, UR, UP). Para estas el campo de fecha puede venir vacío.\n\n"
        "Para 'bcu_listar_monedas' y 'bcu_cotizaciones' especificá el grupo "
        "adecuado; si no se indica, se asume el grupo de divisas (2)."
    )
