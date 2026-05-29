"""Central tool registry powering the meta-discovery layer.

Data-source modules do **not** expose their tools to the MCP client directly.
Instead each tool is registered here with rich metadata, and the server only
exposes a handful of meta-tools (``discover_tools``, ``call_tool``, ...). This
keeps the model's tool list tiny even as the catalog of data tools grows into
the hundreds — the model searches for the right tool, then invokes it by name.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

Handler = Callable[..., Awaitable[Any]]


@dataclass(slots=True)
class ToolSpec:
    name: str
    module: str
    summary: str
    handler: Handler
    params_model: type[BaseModel] | None = None
    keywords: list[str] = field(default_factory=list)

    def schema(self) -> dict[str, Any]:
        """JSON schema for this tool's arguments (empty if it takes none)."""
        if self.params_model is None:
            return {"type": "object", "properties": {}}
        return self.params_model.model_json_schema()

    def search_text(self) -> str:
        return f"{self.name} {self.summary} {' '.join(self.keywords)}".lower()


@dataclass(slots=True)
class ModuleInfo:
    name: str
    title: str
    description: str


# A prompt/resource handler returns a ready-to-use STRING (Spanish prompt or
# markdown document). Handlers may be sync or async; both are supported.
StringHandler = Callable[..., Awaitable[str]] | Callable[..., str]


@dataclass(slots=True)
class PromptSpec:
    """A reusable, parameterizable prompt/instruction (returns a string)."""

    name: str
    module: str
    description: str
    handler: StringHandler


@dataclass(slots=True)
class ResourceSpec:
    """A readable document exposed at a ``uru://<module>/<path>`` URI."""

    uri: str
    name: str
    description: str
    module: str
    handler: StringHandler
    mime_type: str = "text/markdown"


class Registry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._modules: dict[str, ModuleInfo] = {}
        self._prompts: dict[str, PromptSpec] = {}
        self._resources: dict[str, ResourceSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"duplicate tool name: {spec.name}")
        self._tools[spec.name] = spec

    def register_module(self, info: ModuleInfo) -> None:
        self._modules[info.name] = info

    def register_prompt(self, spec: PromptSpec) -> None:
        if spec.name in self._prompts:
            raise ValueError(f"duplicate prompt name: {spec.name}")
        self._prompts[spec.name] = spec

    def register_resource(self, spec: ResourceSpec) -> None:
        if spec.uri in self._resources:
            raise ValueError(f"duplicate resource uri: {spec.uri}")
        self._resources[spec.uri] = spec

    def module_info(self, name: str) -> ModuleInfo | None:
        return self._modules.get(name)

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def all(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def prompts(self) -> list[PromptSpec]:
        return list(self._prompts.values())

    def resources(self) -> list[ResourceSpec]:
        return list(self._resources.values())

    def modules(self) -> dict[str, list[ToolSpec]]:
        out: dict[str, list[ToolSpec]] = {}
        for spec in self._tools.values():
            out.setdefault(spec.module, []).append(spec)
        return out


registry = Registry()


def tool(
    *,
    name: str,
    module: str,
    summary: str,
    params_model: type[BaseModel] | None = None,
    keywords: list[str] | None = None,
) -> Callable[[Handler], Handler]:
    """Decorator that registers an async function as a discoverable tool."""

    def decorator(fn: Handler) -> Handler:
        if not inspect.iscoroutinefunction(fn):
            raise TypeError(f"tool {name} must be an async function")
        registry.register(
            ToolSpec(
                name=name,
                module=module,
                summary=summary,
                handler=fn,
                params_model=params_model,
                keywords=keywords or [],
            )
        )
        return fn

    return decorator


def prompt(
    *,
    name: str,
    module: str,
    description: str,
) -> Callable[[StringHandler], StringHandler]:
    """Register a function as a discoverable MCP prompt.

    The decorated function (sync or async) must return a STRING — a ready-to-use
    prompt/instruction, written in Spanish. Prompt names must be unique.

    Example::

        @prompt(
            name="bcu_resumen_cambiario",
            module="bcu",
            description="Genera un resumen del mercado cambiario.",
        )
        def bcu_resumen_cambiario(moneda: str = "USD") -> str:
            return f"Resumí la cotización de {moneda} frente al peso uruguayo."
    """

    def decorator(fn: StringHandler) -> StringHandler:
        registry.register_prompt(
            PromptSpec(name=name, module=module, description=description, handler=fn)
        )
        return fn

    return decorator


def resource(
    *,
    uri: str,
    name: str,
    description: str,
    module: str,
    mime_type: str = "text/markdown",
) -> Callable[[StringHandler], StringHandler]:
    """Register a function as a readable MCP resource.

    The decorated function (sync or async) must return a STRING (markdown by
    default). Follow the URI convention ``uru://<module>/<path>``; URIs must be
    unique.

    Example::

        @resource(
            uri="uru://bcu/guia-monedas",
            name="Guía de monedas BCU",
            description="Catálogo de códigos de moneda del BCU.",
            module="bcu",
        )
        def guia_monedas() -> str:
            return "# Monedas\\n\\n- USD: dólar estadounidense\\n"
    """

    def decorator(fn: StringHandler) -> StringHandler:
        registry.register_resource(
            ResourceSpec(
                uri=uri,
                name=name,
                description=description,
                module=module,
                handler=fn,
                mime_type=mime_type,
            )
        )
        return fn

    return decorator
