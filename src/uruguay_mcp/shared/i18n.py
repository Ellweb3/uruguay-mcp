"""Minimal bilingual (es/en) message catalog.

Uruguay's audience is Spanish-first, so ``es`` is the default; ``en`` is
provided so the server is usable by non-Spanish speakers. Lookup falls back
to Spanish, then to the raw key, so a missing translation never crashes.
"""

from __future__ import annotations

from .config import settings

_CATALOG: dict[str, dict[str, str]] = {
    "es": {
        "error.upstream": "El servicio {api} devolvió un error: {detail}",
        "error.not_found": "No se encontró: {what}",
        "error.validation": "Argumentos inválidos: {detail}",
        "tool.unknown": "Herramienta desconocida: {name}",
    },
    "en": {
        "error.upstream": "The {api} service returned an error: {detail}",
        "error.not_found": "Not found: {what}",
        "error.validation": "Invalid arguments: {detail}",
        "tool.unknown": "Unknown tool: {name}",
    },
}


def t(key: str, *, lang: str | None = None, **kwargs: object) -> str:
    """Translate ``key`` for the active language, interpolating ``kwargs``."""
    language = lang or settings.lang
    table = _CATALOG.get(language) or _CATALOG["es"]
    template = table.get(key) or _CATALOG["es"].get(key) or key
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template
