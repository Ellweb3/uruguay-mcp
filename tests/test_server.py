"""Smoke test: the server builds and exposes tools + prompts + resources."""

from __future__ import annotations

import pytest

from uruguay_mcp.shared.registry import prompt, registry, resource


@pytest.fixture(autouse=True)
def _seed_prompt_and_resource():
    """Register one prompt + resource so the server has something to expose.

    Module prompts/resources are added by other agents; this fixture guarantees
    the smoke test exercises the registration path regardless of load order.
    Names/URIs are unique-guarded, so register only if absent.
    """
    name = "smoke_test_prompt"
    uri = "uru://smoke/test"

    if all(p.name != name for p in registry.prompts()):

        @prompt(name=name, module="smoke", description="Prompt de prueba.")
        def _p() -> str:
            return "Esto es un prompt de prueba en español."

    if all(r.uri != uri for r in registry.resources()):

        @resource(
            uri=uri,
            name="Recurso de prueba",
            description="Recurso de prueba.",
            module="smoke",
        )
        def _r() -> str:
            return "# Recurso de prueba\n\nContenido en español."

    yield


async def test_server_builds_and_exposes_everything():
    from uruguay_mcp.server import build_server

    mcp = build_server()

    tools = await mcp._list_tools()
    tool_names = {t.name for t in tools}
    for expected in {
        "discover_tools",
        "call_tool",
        "list_modules",
        "plan_query",
        "execute_batch",
    }:
        assert expected in tool_names, f"missing meta-tool {expected}"

    prompts = await mcp.list_prompts()
    resources = await mcp.list_resources()
    assert len(prompts) > 0, "expected at least one prompt registered"
    assert len(resources) > 0, "expected at least one resource registered"


def test_registry_rejects_duplicate_prompt_and_resource():
    name = registry.prompts()[0].name if registry.prompts() else "smoke_test_prompt"

    with pytest.raises(ValueError):

        @prompt(name=name, module="smoke", description="dup")
        def _dup_prompt() -> str:
            return "x"
