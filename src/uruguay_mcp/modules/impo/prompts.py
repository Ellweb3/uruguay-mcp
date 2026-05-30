"""Prompts reutilizables para el módulo IMPO (normativa nacional)."""

from __future__ import annotations

from ...shared.registry import prompt
from .constants import MODULE


@prompt(
    name="impo_consultar_norma",
    module=MODULE,
    description="Instrucción para obtener el texto de una norma nacional por tipo/número/año.",
)
def impo_consultar_norma(tipo: str = "ley", numero: str = "", anio: str = "") -> str:
    ident = (
        f"{tipo} {numero}/{anio}".strip()
        if tipo != "constitucion"
        else f"constitución {anio}".strip()
    )
    return (
        f"Obtené el texto de la norma ({ident}) con la herramienta impo_get_norma "
        "(parámetros tipo, numero y anio; el año debe tener 4 dígitos). Para la "
        "constitución omití numero. Resumí los metadatos (nombreNorma, fechas, "
        "leyenda) y listá los artículos relevantes con su texto. Si querés el "
        "texto tal como se publicó usá version='original'."
    )


@prompt(
    name="impo_diario_del_dia",
    module=MODULE,
    description="Instrucción para obtener el Diario Oficial de una fecha (PDF por sección).",
)
def impo_diario_del_dia(fecha: str | None = None) -> str:
    cuando = f"del {fecha}" if fecha else "de hoy"
    return (
        f"Obtené el Diario Oficial {cuando} con la herramienta impo_diario_oficial "
        "(parámetro fecha en formato YYYY-MM-DD; por defecto hoy). Devolvé los "
        "enlaces PDF de cada sección (indice, documentos, avisos, um) y aclarale "
        "al usuario que el Diario Oficial es sólo PDF, sin API JSON."
    )


@prompt(
    name="impo_buscar_normativa_guia",
    module=MODULE,
    description="Instrucción para buscar normativa en IMPO con degradación elegante.",
)
def impo_buscar_normativa_guia(query: str = "") -> str:
    return (
        f"Buscá normativa sobre '{query}' con la herramienta impo_buscar_normativa. "
        "Tené en cuenta que IMPO no tiene una API JSON de búsqueda: si la consulta "
        "menciona un tipo/número/año la herramienta resuelve directo a impo_get_norma; "
        "si no, devuelve URLs canónicas de búsqueda. Cuando conozcas tipo, número y "
        "año, preferí impo_get_norma para datos estructurados."
    )


@prompt(
    name="impo_buscar_texto_guia",
    module=MODULE,
    description="Instrucción para hacer búsqueda full-text real en IMPO por tema.",
)
def impo_buscar_texto_guia(query: str = "") -> str:
    return (
        f"Buscá en el sitio de IMPO sobre '{query}' con la herramienta "
        "impo_buscar_texto (parámetros query, pagina y max_resultados). Es una "
        "búsqueda full-text real (feed RSS de WordPress) que devuelve titulo, url, "
        "fecha, autor y categorias. Si el usuario quiere las últimas publicaciones "
        "o anuncios de nuevas leyes, usá impo_novedades. Cuando identifiques una "
        "norma puntual (tipo/número/año), pasá a impo_get_norma; y para ver qué "
        "otras normas la referencian usá impo_referencias_norma."
    )
