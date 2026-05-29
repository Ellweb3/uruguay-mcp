# uruguay-mcp

MCP server that gives AI agents structured access to **Uruguay's open
government data**: a meta-discovery layer over modular, per-source data tools.

## Why a meta-discovery layer?

Instead of flooding the model with hundreds of tool definitions, the server
exposes **five meta-tools**. The model searches for what it needs, then invokes
the matching data tool by name. The prompt-visible surface stays constant no
matter how many data sources are added.

| Meta-tool | Purpose |
|---|---|
| `discover_tools(query, module?, limit?)` | Rank data tools relevant to a natural-language need (returns their argument schemas) |
| `call_tool(name, arguments)` | Invoke a data tool by name (validates arguments) |
| `list_modules()` | List data-source modules and their tool counts |
| `plan_query(goal)` | Surface candidate tools for a multi-step goal |
| `execute_batch(calls)` | Run several calls concurrently with per-call error isolation |

Every tool returns a unified envelope: `{ "_meta": { source, cached, lang, timestamp }, "data": ... }`
(`timestamp` is a UTC ISO-8601 stamp added on every response).

At a glance the server currently exposes **5 meta-tools + 31 data tools across
6 modules**, plus **17 prompts** and **11 resources** (see below).

## Data sources (modules)

| Module | Source | Protocol | Tools | Status |
|---|---|---|---|---|
| `catalogodatos` | [catalogodatos.gub.uy](https://catalogodatos.gub.uy) — national CKAN catalog (~2680 datasets, 72 orgs) | CKAN REST | 5 | ✅ implemented |
| `bcu` | Banco Central del Uruguay — exchange rates | SOAP (`zeep`) | 4 | ✅ implemented |
| `ine` | Instituto Nacional de Estadística — ANDA / microdata | REST | 3 | ✅ implemented |
| `gubuy` | gub.uy public API / service catalog (CKAN showcase) | CKAN REST | 4 | ✅ implemented |
| `montevideo` | Intendencia de Montevideo — own CKAN + realtime transport API | CKAN + REST | 11 | ✅ implemented |
| `datastore` | Cross-source SQLite workspace — load CSV/CKAN resources into tables and run read-only SQL (JOINs across sources) | local SQLite | 4 | ✅ implemented |

The transport surface of the `montevideo` module needs OAuth2 client
credentials (`URUGUAY_MCP_MVD_CLIENT_ID` / `URUGUAY_MCP_MVD_CLIENT_SECRET`); without
them the transport tools return a typed `validation_error` envelope while the
CKAN tools work unauthenticated.

The `datastore` module loads tabular data (a CSV URL or a CKAN resource) into a
process-wide in-memory SQLite store, then runs **read-only** `SELECT`s across the
loaded tables — the practical way to JOIN records from two different APIs. It is
loaded by default.

## Prompts & Resources

Besides tools, each module registers reusable **prompts** (parameterized,
Spanish instruction templates) and **resources** (static reference docs under
the `uru://<module>/<path>` URI scheme). Both are exposed natively through
FastMCP, so any MCP client can list and render them.

- **17 prompts** — e.g. `bcu_cotizacion_dolar_hoy`, `catalogo_buscar_por_tema`,
  `ine_buscar_estudios`, `montevideo_proximo_bus`, `gubuy_buscar_servicios`,
  `datastore_unir_dos_fuentes`.
- **11 resources** — e.g. `uru://bcu/codigos-moneda`,
  `uru://catalogodatos/guia-de-uso`, `uru://ine/guia-fuentes`,
  `uru://montevideo/credenciales-transporte`, `uru://datastore/guia-uso`.

See **[EXAMPLES.md](EXAMPLES.md)** for 12 end-to-end usage scenarios (including
cross-source ones via `plan_query` / `execute_batch` and SQL JOINs through the
`datastore` module).

## Architecture

```
src/uruguay_mcp/
├── server.py            # FastMCP wiring; meta-tools + registered prompts + resources
├── cli.py               # `uruguay-mcp [serve]` / `uruguay-mcp install`; -v/--debug logging
├── meta/                # discovery layer
│   ├── tools.py         # the 5 meta-tools
│   └── search.py        # BM25-lite ranking over the registry
├── shared/              # reused by every module
│   ├── config.py        # env-driven settings (URUGUAY_MCP_*)
│   ├── http.py          # async client: retries (tenacity) + rate limit
│   ├── cache.py         # async TTL cache
│   ├── rate_limiter.py  # per-host token bucket
│   ├── envelope.py      # unified {_meta, data} response (+ UTC timestamp)
│   ├── i18n.py          # es/en messages
│   ├── errors.py        # typed, localized errors
│   └── registry.py      # tool/prompt/resource + module registry; @tool/@prompt/@resource
└── modules/             # one self-contained package per data source
    ├── catalogodatos/   # constants · schemas · client · tools · prompts · resources
    ├── bcu/             # Banco Central del Uruguay (SOAP via zeep)
    ├── ine/             # INE — ANDA studies + CKAN fallback
    ├── gubuy/           # gub.uy service/API catalog (CKAN showcase)
    ├── montevideo/      # IM CKAN portal + realtime transport API (OAuth2)
    └── datastore/       # cross-source SQLite workspace (load + read-only SQL)
```

Each module package is independent: `constants.py` (URLs/limits), `schemas.py`
(Pydantic argument models = advertised JSON schema), `client.py` (async API
wrapper), `tools.py` (`@tool`-decorated handlers), and optionally `prompts.py` /
`resources.py` (`@prompt` / `@resource` decorators). Importing the package
self-registers its tools, prompts and resources.

## Install & run

```bash
uv venv
uv pip install -e ".[dev]"

# stdio (Claude Desktop / Claude Code)
uruguay-mcp

# SSE / HTTP
uruguay-mcp --transport sse --port 8000

# load only specific modules
uruguay-mcp --modules catalogodatos
# or: URUGUAY_MCP_MODULES=catalogodatos uruguay-mcp

# verbose / debug logging (to stderr)
uruguay-mcp --verbose      # INFO
uruguay-mcp --debug        # DEBUG
```

### One-command install

`uruguay-mcp install` merges the server into Claude Desktop's config (preserving any
existing `mcpServers` and unrelated keys) and prints a ready-to-paste snippet for
Claude Code / Cursor:

```bash
uruguay-mcp install
```

On macOS it writes to
`~/Library/Application Support/Claude/claude_desktop_config.json`; on
Windows to `%APPDATA%\Claude\...`; on Linux to `~/.config/Claude/...`. Restart
the client afterwards.

### Claude Desktop config (manual)

```json
{
  "mcpServers": {
    "uruguay-mcp": { "command": "uruguay-mcp" }
  }
}
```

## Configuration

All via `URUGUAY_MCP_*` environment variables (see `shared/config.py`):

| Variable | Default | Meaning |
|---|---|---|
| `URUGUAY_MCP_LANG` | `es` | Language for human-facing strings (`es`/`en`) |
| `URUGUAY_MCP_HTTP_TIMEOUT` | `30` | HTTP timeout (seconds) |
| `URUGUAY_MCP_CACHE_TTL` | `900` | Response cache TTL (seconds) |
| `URUGUAY_MCP_RATE_LIMIT_RPS` | `5` | Max requests/sec per host |
| `URUGUAY_MCP_MODULES` | _(all)_ | Comma-separated module allowlist |
| `URUGUAY_MCP_MVD_CLIENT_ID` | _(unset)_ | OAuth2 client id for the Montevideo transport API |
| `URUGUAY_MCP_MVD_CLIENT_SECRET` | _(unset)_ | OAuth2 client secret for the Montevideo transport API |

## Development

```bash
uv run pytest                      # unit tests (HTTP mocked, offline)
uv run pytest -m integration       # hits live government APIs
uv run ruff check src tests
uv run pyright
```

## License

MIT
