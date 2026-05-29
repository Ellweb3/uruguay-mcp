"""Command-line entry point: ``uruguay-mcp`` (serve) and ``uruguay-mcp install``."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import structlog

from .server import build_server
from .shared.config import settings


def _configure_logging(*, verbose: bool, debug: bool) -> None:
    """Wire structlog/stdlib logging to the requested verbosity."""
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(
        level=level, format="%(message)s", stream=sys.stderr, force=True
    )
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )


def _add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable INFO-level logging"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable DEBUG-level logging"
    )


def _config_snippet(command: str = "uruguay-mcp") -> dict[str, Any]:
    """The MCP server block other clients expect under ``mcpServers``."""
    return {"command": command, "args": [], "env": {}}


def _claude_desktop_config_path() -> Path | None:
    """Best-effort location of Claude Desktop's config on this platform."""
    if sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
    if sys.platform.startswith("win"):
        import os

        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Claude" / "claude_desktop_config.json"
        return None
    # Linux / other: Claude Desktop is unofficial; use the XDG-style path.
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def _install(args: argparse.Namespace) -> int:
    """Write/update the Claude Desktop config; print snippets for other clients."""
    server_name = "uruguay-mcp"
    block = _config_snippet()
    snippet = {"mcpServers": {server_name: block}}

    print("MCP server config snippet (Claude Code / Cursor):")
    print(json.dumps(snippet, indent=2))
    print()

    path = _claude_desktop_config_path()
    if path is None:
        print(
            "Could not determine Claude Desktop config path on this platform.\n"
            "Add the snippet above to your client's MCP config manually."
        )
        return 0

    if path.exists():
        try:
            config = json.loads(path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            print(f"Existing config at {path} is not valid JSON; not modifying.")
            print("Merge the snippet above manually.")
            return 1
    else:
        config = {}

    # Merge without clobbering unrelated keys.
    servers = config.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        print(f"'mcpServers' in {path} is not an object; not modifying.")
        return 1
    servers[server_name] = block

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Updated Claude Desktop config: {path}")
    print("Restart Claude Desktop to load the uruguay-mcp server.")
    return 0


def _serve(args: argparse.Namespace) -> int:
    if args.modules is not None:
        settings.modules = args.modules

    mcp = build_server()

    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="uruguay-mcp", description="MCP server for Uruguay open data"
    )
    _add_common_flags(parser)

    # Serve flags live on the top-level parser too, so bare `uruguay-mcp` still serves.
    parser.add_argument(
        "--transport", choices=["stdio", "sse", "http"], default="stdio"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port for sse/http transports"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host for sse/http transports"
    )
    parser.add_argument(
        "--modules",
        default=None,
        help="Comma-separated module allowlist (overrides URUGUAY_MCP_MODULES)",
    )

    sub = parser.add_subparsers(dest="command")
    install_parser = sub.add_parser(
        "install", help="Write/print MCP client config for uruguay-mcp"
    )
    _add_common_flags(install_parser)

    args = parser.parse_args()

    _configure_logging(verbose=args.verbose, debug=args.debug)

    if args.command == "install":
        raise SystemExit(_install(args))

    raise SystemExit(_serve(args))


if __name__ == "__main__":
    main()
