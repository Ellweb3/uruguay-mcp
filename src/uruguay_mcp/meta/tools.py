"""The meta-tools exposed to the MCP client.

Only these five functions are visible to the model. Everything a data-source
module offers is reached *through* them: discover → call. This keeps the
prompt-visible tool surface constant regardless of how many modules load.
"""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from ..shared import errors
from ..shared.envelope import error_envelope
from ..shared.registry import registry
from . import search as search_mod


def _spec_brief(spec, *, with_schema: bool = False) -> dict[str, Any]:
    out = {
        "name": spec.name,
        "module": spec.module,
        "summary": spec.summary,
        "keywords": spec.keywords,
    }
    if with_schema:
        out["arguments"] = spec.schema()
    return out


async def discover_tools(query: str, module: str | None = None, limit: int = 8) -> dict[str, Any]:
    """Find data tools relevant to a natural-language need.

    Returns ranked tools with their argument schemas. Use this first, then
    invoke the chosen tool via ``call_tool``.
    """
    results = search_mod.search(query, limit=limit, module=module)
    return {
        "query": query,
        "matches": [
            {**_spec_brief(spec, with_schema=True), "score": score}
            for spec, score in results
        ],
        "hint": "Call the chosen tool with call_tool(name, arguments).",
    }


async def list_modules() -> dict[str, Any]:
    """List the available data-source modules and how many tools each offers."""
    grouped = registry.modules()
    modules = []
    for name, specs in sorted(grouped.items()):
        info = registry.module_info(name)
        modules.append(
            {
                "name": name,
                "title": info.title if info else name,
                "description": info.description if info else "",
                "tool_count": len(specs),
            }
        )
    return {"modules": modules, "total_tools": sum(len(s) for s in grouped.values())}


async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> Any:
    """Invoke a data tool by name with the given arguments."""
    spec = registry.get(name)
    if spec is None:
        return error_envelope("not_found", f"Unknown tool: {name}")

    arguments = arguments or {}
    if spec.params_model is not None:
        try:
            model = spec.params_model.model_validate(arguments)
        except PydanticValidationError as exc:
            return error_envelope(
                "validation_error", "Invalid arguments", details={"errors": exc.errors()}
            )
        kwargs = model.model_dump()
    else:
        kwargs = {}

    try:
        return await spec.handler(**kwargs)
    except errors.UruMcpError as exc:
        return error_envelope(exc.code, exc.message, details=exc.details)


async def plan_query(goal: str) -> dict[str, Any]:
    """Sketch a plan: surface candidate tools across modules for a broad goal.

    For multi-step needs, this returns the most relevant tools so the model can
    chain them (e.g. search a dataset, then query its datastore).
    """
    results = search_mod.search(goal, limit=10)
    return {
        "goal": goal,
        "candidate_tools": [_spec_brief(spec) for spec, _ in results],
        "hint": "Chain tools with call_tool / execute_batch; many lookups need a search first.",
    }


async def execute_batch(calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Run several tool calls concurrently with per-call error isolation.

    ``calls`` is a list of ``{"name": ..., "arguments": {...}}``. A failure in
    one call does not abort the others.
    """

    async def _one(call: dict[str, Any]) -> Any:
        return await call_tool(call.get("name", ""), call.get("arguments"))

    results = await asyncio.gather(*(_one(c) for c in calls), return_exceptions=True)
    return {
        "results": [
            error_envelope("error", str(r)) if isinstance(r, Exception) else r
            for r in results
        ]
    }


META_TOOLS = [discover_tools, list_modules, call_tool, plan_query, execute_batch]
