"""FastMCP server wiring.

The server exposes only the five meta-tools. Data-source modules register their
tools into the registry on import; the model reaches them via discover/call.
"""

from __future__ import annotations

import structlog
from fastmcp import FastMCP
from fastmcp.prompts import Prompt
from fastmcp.resources import FunctionResource

from .meta.tools import META_TOOLS
from .modules import load_modules
from .shared.registry import PromptSpec, ResourceSpec, registry

log = structlog.get_logger()

INSTRUCTIONS = """\
Servidor MCP de datos abiertos de Uruguay. No expone cientos de herramientas
directamente: usá `discover_tools("lo que buscás")` para encontrar la herramienta
adecuada y luego `call_tool(name, arguments)` para ejecutarla. `list_modules`
muestra las fuentes de datos disponibles; `execute_batch` corre varias llamadas
en paralelo.
"""


def _register_prompt(mcp: FastMCP, spec: PromptSpec) -> None:
    """Expose a registry PromptSpec through FastMCP's prompt API."""
    prompt = Prompt.from_function(
        spec.handler,
        name=spec.name,
        description=spec.description,
        tags={spec.module},
    )
    mcp.add_prompt(prompt)


def _register_resource(mcp: FastMCP, spec: ResourceSpec) -> None:
    """Expose a registry ResourceSpec through FastMCP's resource API."""
    resource = FunctionResource.from_function(
        spec.handler,
        uri=spec.uri,
        name=spec.name,
        description=spec.description,
        mime_type=spec.mime_type,
        tags={spec.module},
    )
    mcp.add_resource(resource)


def build_server() -> FastMCP:
    loaded = load_modules()
    mcp = FastMCP(name="uruguay-mcp", instructions=INSTRUCTIONS)

    for fn in META_TOOLS:
        mcp.tool(fn)

    for prompt_spec in registry.prompts():
        _register_prompt(mcp, prompt_spec)

    for resource_spec in registry.resources():
        _register_resource(mcp, resource_spec)

    log.info(
        "uruguay-mcp ready",
        modules=loaded,
        data_tools=len(registry.all()),
        meta_tools=len(META_TOOLS),
        prompts=len(registry.prompts()),
        resources=len(registry.resources()),
    )
    return mcp
