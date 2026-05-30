"""Data-source modules. Importing a module registers its tools."""

from __future__ import annotations

import importlib

from ..shared.config import settings

# Modules are listed here; the loader respects URUGUAY_MCP_MODULES allowlist.
ALL_MODULES = [
    "catalogodatos",
    "bcu",
    "ine",
    "gubuy",
    "montevideo",
    "datastore",
    "acce",
    "impo",
    "inumet",
    "parlamento",
    "ide",
    "educacion",
    "salud",
    "mides",
    "noticias",
]


def load_modules() -> list[str]:
    """Import enabled module packages so their tools self-register."""
    allow = settings.enabled_modules()
    loaded: list[str] = []
    for name in ALL_MODULES:
        if allow is not None and name not in allow:
            continue
        importlib.import_module(f"{__name__}.{name}")
        loaded.append(name)
    return loaded
