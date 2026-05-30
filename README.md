<div align="center">

<img src="https://flagcdn.com/w160/uy.png" alt="Bandera de Uruguay" width="120" />

# 🇺🇾 uruguay-mcp

**Structured AI-agent access to Uruguay's open government data**
<br>
*Acceso estructurado de agentes de IA a los datos abiertos del Estado uruguayo*

[![PyPI](https://img.shields.io/pypi/v/uruguay-mcp?color=blue&label=PyPI)](https://pypi.org/project/uruguay-mcp/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-7C3AED)](https://modelcontextprotocol.io/)
[![Tests](https://img.shields.io/badge/tests-129%20passing-brightgreen)](#development)
[![Coverage](https://img.shields.io/badge/coverage-88%25-brightgreen)](#development)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

🌎 **[Español](README.es.md)** · **English**

</div>

---

An [MCP](https://modelcontextprotocol.io/) server that gives AI agents structured
access to **Uruguay's open government data** — the national data catalog, the
Central Bank, the statistics institute, Montevideo's city data & realtime
transport, and the gub.uy service catalog — behind a single **meta-discovery**
layer.

## ✨ Why a meta-discovery layer?

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

Every tool returns a unified envelope: `{ "_meta": { source, cached, lang, timestamp }, "data": ... }`.

> At a glance: **5 meta-tools + 49 data tools across 10 modules**, plus **29
> prompts** and **19 resources**.

## 📚 Data sources (modules)

| | Module | Source | Protocol | Tools |
|---|---|---|---|:--:|
| 🏛️ | `catalogodatos` | [catalogodatos.gub.uy](https://catalogodatos.gub.uy) — national CKAN catalog (~2680 datasets, 72 orgs) + DataStore SQL | CKAN REST | 9 |
| 💵 | `bcu` | Banco Central del Uruguay — exchange rates | SOAP (`zeep`) | 4 |
| 📊 | `ine` | Instituto Nacional de Estadística — ANDA / microdata | REST | 3 |
| 🌐 | `gubuy` | gub.uy public API / service catalog | CKAN REST | 4 |
| 🚌 | `montevideo` | Intendencia de Montevideo — city CKAN + realtime transport | CKAN + REST | 11 |
| 🗄️ | `datastore` | Cross-source SQLite workspace — load CSV/CKAN data, run read-only SQL JOINs | local SQLite | 4 |
| 🛒 | `acce` | Agencia de Compras y Contrataciones del Estado — public procurement (OCDS) | OCDS REST/RSS + CKAN | 4 |
| ⚖️ | `impo` | IMPO — legislation, normativa & Diario Oficial | REST (JSON) | 3 |
| 🌦️ | `inumet` | Instituto Uruguayo de Meteorología — stations, forecast & alerts | REST + HTML | 3 |
| 🏛️ | `parlamento` | Parlamento del Uruguay — datasets, attendance & activity (CKAN-backed) | CKAN REST | 4 |

The transport surface of `montevideo` needs OAuth2 credentials
(`URUGUAY_MCP_MVD_CLIENT_ID` / `URUGUAY_MCP_MVD_CLIENT_SECRET`); without them the
transport tools return a typed `validation_error` while the CKAN tools work
unauthenticated.

## 🧩 Prompts & Resources

Each module also registers reusable **prompts** (parameterized Spanish
instruction templates) and **resources** (static reference docs under the
`uru://<module>/<path>` URI scheme), exposed natively through FastMCP.

- **29 prompts** — e.g. `bcu_cotizacion_dolar_hoy`, `catalogo_buscar_por_tema`,
  `ine_buscar_estudios`, `montevideo_proximo_bus`, `datastore_unir_dos_fuentes`,
  `acce_analizar_compra`, `impo_consultar_norma`, `inumet_clima_actual`.
- **19 resources** — e.g. `uru://bcu/codigos-moneda`,
  `uru://catalogodatos/guia-de-uso`, `uru://montevideo/credenciales-transporte`,
  `uru://acce/glosario-ocds`, `uru://impo/esquema`, `uru://inumet/variables`.

See **[EXAMPLES.md](EXAMPLES.md)** for end-to-end usage scenarios, including
cross-source ones via `plan_query` / `execute_batch` and SQL JOINs through the
`datastore` module.

## 🚀 Quick start

```bash
# Run directly from PyPI (once published)
uvx uruguay-mcp

# …or install it
pip install uruguay-mcp        # or: uv pip install uruguay-mcp
uruguay-mcp
```

### One-command install into Claude

```bash
uruguay-mcp install
```

Merges the server into Claude Desktop's config (preserving existing
`mcpServers` and unrelated keys) and prints a ready-to-paste snippet for Claude
Code / Cursor. Restart the client afterwards.

### Claude Desktop config (manual)

```json
{
  "mcpServers": {
    "uruguay-mcp": { "command": "uruguay-mcp" }
  }
}
```

### Run options

```bash
uruguay-mcp                          # stdio (default)
uruguay-mcp --transport sse --port 8000
uruguay-mcp --modules catalogodatos,bcu   # load only some modules
uruguay-mcp --verbose                # INFO logs   (--debug for DEBUG)
```

## ⚙️ Configuration

All via `URUGUAY_MCP_*` environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `URUGUAY_MCP_LANG` | `es` | Language for human-facing strings (`es`/`en`) |
| `URUGUAY_MCP_HTTP_TIMEOUT` | `30` | HTTP timeout (seconds) |
| `URUGUAY_MCP_CACHE_TTL` | `900` | Response cache TTL (seconds) |
| `URUGUAY_MCP_RATE_LIMIT_RPS` | `5` | Max requests/sec per host |
| `URUGUAY_MCP_MODULES` | _(all)_ | Comma-separated module allowlist |
| `URUGUAY_MCP_MVD_CLIENT_ID` | _(unset)_ | OAuth2 client id for the Montevideo transport API |
| `URUGUAY_MCP_MVD_CLIENT_SECRET` | _(unset)_ | OAuth2 client secret for the Montevideo transport API |

## 🏗️ Architecture

```
src/uruguay_mcp/
├── server.py            # FastMCP wiring; meta-tools + registered prompts + resources
├── cli.py               # `uruguay-mcp` / `uruguay-mcp install`; -v/--debug logging
├── meta/                # discovery layer
│   ├── tools.py         # the 5 meta-tools
│   └── search.py        # BM25-lite ranking over the registry
├── shared/              # reused by every module
│   ├── config.py        # env-driven settings (URUGUAY_MCP_*)
│   ├── http.py          # async client: retries (tenacity) + per-host rate limit
│   ├── cache.py         # async TTL cache
│   ├── envelope.py      # unified {_meta, data} response (+ UTC timestamp)
│   ├── i18n.py          # es/en messages
│   ├── errors.py        # typed, localized errors
│   └── registry.py      # tool/prompt/resource registry; @tool/@prompt/@resource
└── modules/             # one self-contained package per data source
    ├── catalogodatos/   ├── bcu/          ├── ine/
    ├── gubuy/           ├── montevideo/   ├── datastore/
    ├── acce/            ├── impo/         ├── inumet/
    └── parlamento/
```

Each module package is independent (`constants` · `schemas` · `client` ·
`tools` · optional `prompts`/`resources`). Importing the package self-registers
everything it offers.

## 🛠️ Development

```bash
uv venv && uv pip install -e ".[dev]"

uv run pytest                  # 129 unit tests (HTTP mocked, offline) · 88% coverage
uv run pytest -m integration   # hits live government APIs
uv run ruff check src tests
uv run pyright
```

## 🙌 Acknowledgements

Built on data published by **AGESIC**, **BCU**, **INE** and the **Intendencia de
Montevideo** under Uruguay's open-data law (Nº 18.381). This project is an
independent client and is not affiliated with those institutions.

## 📄 License

[MIT](LICENSE)
