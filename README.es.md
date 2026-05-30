<div align="center">

<img src="https://flagcdn.com/w160/uy.png" alt="Bandera de Uruguay" width="120" />

# 🇺🇾 uruguay-mcp

**Acceso estructurado de agentes de IA a los datos abiertos del Estado uruguayo**
<br>
*Structured AI-agent access to Uruguay's open government data*

[![PyPI](https://img.shields.io/pypi/v/uruguay-mcp?color=blue&label=PyPI)](https://pypi.org/project/uruguay-mcp/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-7C3AED)](https://modelcontextprotocol.io/)
[![CI](https://github.com/Ellweb3/uruguay-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Ellweb3/uruguay-mcp/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-240%20passing-brightgreen)](#desarrollo)
[![Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen)](#desarrollo)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

🌎 **Español** · **[English](README.md)**

</div>

---

Un servidor [MCP](https://modelcontextprotocol.io/) que le da a los agentes de IA
acceso estructurado a los **datos abiertos del Estado uruguayo** — el catálogo
nacional de datos, el Banco Central, el Instituto Nacional de Estadística, los
datos y el transporte en tiempo real de Montevideo, datos espaciales (IDE),
educación, salud, programas sociales, seguridad social (BPS), noticias de
gobierno, y el catálogo de servicios gub.uy — detrás de una única capa de
**meta-descubrimiento**.

## ✨ ¿Por qué una capa de meta-descubrimiento?

En lugar de inundar al modelo con cientos de definiciones de herramientas, el
servidor expone **cinco meta-herramientas**. El modelo busca lo que necesita y
luego invoca la herramienta de datos correspondiente por su nombre. La superficie
visible en el prompt se mantiene constante sin importar cuántas fuentes se agreguen.

| Meta-herramienta | Para qué sirve |
|---|---|
| `discover_tools(query, module?, limit?)` | Ordena las herramientas relevantes a una necesidad en lenguaje natural (devuelve sus esquemas de argumentos) |
| `call_tool(name, arguments)` | Invoca una herramienta por nombre (valida los argumentos) |
| `list_modules()` | Lista los módulos de fuentes de datos y su cantidad de herramientas |
| `plan_query(goal)` | Sugiere herramientas candidatas para un objetivo de varios pasos |
| `execute_batch(calls)` | Ejecuta varias llamadas en paralelo, aislando errores por llamada |

Cada herramienta devuelve un sobre unificado: `{ "_meta": { source, cached, lang, timestamp }, "data": ... }`.

> En resumen: **5 meta-herramientas + 80 herramientas de datos en 16 módulos**,
> más **52 prompts** y **34 recursos**.

## 📚 Fuentes de datos (módulos)

| | Módulo | Fuente | Protocolo | Herramientas |
|---|---|---|---|:--:|
| 🏛️ | `catalogodatos` | [catalogodatos.gub.uy](https://catalogodatos.gub.uy) — catálogo nacional CKAN (~2680 datasets, 72 organismos) + SQL sobre DataStore | CKAN REST | 9 |
| 💵 | `bcu` | Banco Central del Uruguay — cotizaciones | SOAP (`zeep`) | 4 |
| 📊 | `ine` | Instituto Nacional de Estadística — estudios ANDA + consultas al DataStore (CKAN nacional) | REST | 7 |
| 🌐 | `gubuy` | gub.uy — catálogo de servicios y APIs del Estado | CKAN REST | 4 |
| 🚌 | `montevideo` | Intendencia de Montevideo — CKAN municipal + transporte en tiempo real | CKAN + REST | 11 |
| 🗄️ | `datastore` | Espacio SQLite multi-fuente — cargar datos CSV/CKAN y correr SQL de solo lectura (JOINs entre fuentes) | SQLite local | 4 |
| 🛒 | `acce` | Agencia de Compras y Contrataciones del Estado — compras públicas (OCDS) | OCDS REST/RSS + CKAN | 4 |
| ⚖️ | `impo` | IMPO — legislación, normativa y Diario Oficial | REST (JSON) | 6 |
| 🌦️ | `inumet` | Instituto Uruguayo de Meteorología — estaciones, pronóstico y alertas | REST + HTML | 3 |
| 🏛️ | `parlamento` | Parlamento del Uruguay — datasets, asistencias y actividades (vía CKAN) | CKAN REST | 4 |
| 🗺️ | `ide` | IDE Uruguay (AGESIC) — datos espaciales: capas WFS, parcelas catastrales y geocodificación | WFS 2.0 + REST | 5 |
| 🎓 | `educacion` | ANEP / educación — datasets y directorios de centros (CKAN nacional, org=anep) | CKAN REST | 3 |
| 🏥 | `salud` | Salud (MSP / FNR) — datasets de salud, policlínicas y gasto en medicamentos | CKAN REST | 5 |
| 🤝 | `mides` | MIDES — programas sociales y la *Guía de Recursos* de servicios | CKAN + HTML | 4 |
| 🧓 | `bps` | Banco de Previsión Social — observatorio "BPS en Cifras": pasividades, prestaciones y cotizantes (indicadores en vivo) | REST (JSON) | 5 |
| 📰 | `noticias` | Noticias de gobierno gub.uy — últimas publicaciones y búsqueda de texto | scraping HTML | 2 |

La parte de transporte de `montevideo` requiere credenciales OAuth2
(`URUGUAY_MCP_MVD_CLIENT_ID` / `URUGUAY_MCP_MVD_CLIENT_SECRET`); sin ellas, las
herramientas de transporte devuelven un `validation_error` tipado, mientras que
las de CKAN funcionan sin autenticación.

## 🧩 Prompts y recursos

Cada módulo también registra **prompts** reutilizables (plantillas de instrucción
en español, parametrizadas) y **recursos** (documentos de referencia estáticos
bajo el esquema de URI `uru://<módulo>/<ruta>`), expuestos de forma nativa a
través de FastMCP.

- **52 prompts** — p. ej. `bcu_cotizacion_dolar_hoy`, `catalogo_buscar_por_tema`,
  `bps_pasividades_actuales`,
  `ine_buscar_estudios`, `montevideo_proximo_bus`, `datastore_unir_dos_fuentes`,
  `acce_analizar_compra`, `impo_consultar_norma`, `inumet_clima_actual`,
  `ide_consultar_catastro`, `salud_consultar_medicamentos`, `noticias_ultimas`.
- **34 recursos** — p. ej. `uru://bcu/codigos-moneda`, `uru://bps/catalogo-indicadores`,
  `uru://catalogodatos/guia-de-uso`, `uru://montevideo/credenciales-transporte`,
  `uru://acce/glosario-ocds`, `uru://impo/esquema`, `uru://inumet/variables`,
  `uru://ide/capas-destacadas`, `uru://salud/fuentes`, `uru://mides/guia-recursos`.

Mirá **[EXAMPLES.md](EXAMPLES.md)** para escenarios de uso de punta a punta,
incluidos los que combinan fuentes mediante `plan_query` / `execute_batch` y
JOINs SQL con el módulo `datastore`.

## 🚀 Inicio rápido

```bash
# Ejecutar directo desde PyPI (una vez publicado)
uvx uruguay-mcp

# …o instalarlo
pip install uruguay-mcp        # o: uv pip install uruguay-mcp
uruguay-mcp
```

### Instalación en Claude con un comando

```bash
uruguay-mcp install
```

Agrega el servidor a la configuración de Claude Desktop (preservando los
`mcpServers` existentes y otras claves) e imprime un fragmento listo para pegar
en Claude Code / Cursor. Reiniciá el cliente después.

### Configuración de Claude Desktop (manual)

```json
{
  "mcpServers": {
    "uruguay-mcp": { "command": "uruguay-mcp" }
  }
}
```

### Opciones de ejecución

```bash
uruguay-mcp                          # stdio (por defecto)
uruguay-mcp --transport sse --port 8000
uruguay-mcp --modules catalogodatos,bcu   # cargar solo algunos módulos
uruguay-mcp --verbose                # logs INFO   (--debug para DEBUG)
```

## ⚙️ Configuración

Todo mediante variables de entorno `URUGUAY_MCP_*`:

| Variable | Por defecto | Significado |
|---|---|---|
| `URUGUAY_MCP_LANG` | `es` | Idioma de los textos para humanos (`es`/`en`) |
| `URUGUAY_MCP_HTTP_TIMEOUT` | `30` | Timeout HTTP (segundos) |
| `URUGUAY_MCP_CACHE_TTL` | `900` | TTL de la caché de respuestas (segundos) |
| `URUGUAY_MCP_RATE_LIMIT_RPS` | `5` | Máximo de solicitudes/seg por host |
| `URUGUAY_MCP_MODULES` | _(todos)_ | Lista de módulos a cargar (separados por coma) |
| `URUGUAY_MCP_MVD_CLIENT_ID` | _(sin valor)_ | client id OAuth2 del transporte de Montevideo |
| `URUGUAY_MCP_MVD_CLIENT_SECRET` | _(sin valor)_ | client secret OAuth2 del transporte de Montevideo |

## 🏗️ Arquitectura

```
src/uruguay_mcp/
├── server.py            # Integración FastMCP; meta-tools + prompts + recursos
├── cli.py               # `uruguay-mcp` / `uruguay-mcp install`; logs -v/--debug
├── meta/                # capa de descubrimiento
│   ├── tools.py         # las 5 meta-herramientas
│   └── search.py        # ranking BM25-lite sobre el registro
├── shared/              # reutilizado por cada módulo
│   ├── config.py        # settings por entorno (URUGUAY_MCP_*)
│   ├── http.py          # cliente async: reintentos (tenacity) + rate limit por host
│   ├── cache.py         # caché async con TTL
│   ├── envelope.py      # respuesta unificada {_meta, data} (+ timestamp UTC)
│   ├── i18n.py          # mensajes es/en
│   ├── errors.py        # errores tipados y localizados
│   └── registry.py      # registro de tool/prompt/resource; @tool/@prompt/@resource
└── modules/             # un paquete autónomo por fuente de datos
    ├── catalogodatos/   ├── bcu/          ├── ine/
    ├── gubuy/           ├── montevideo/   ├── datastore/
    ├── acce/            ├── impo/         ├── inumet/
    ├── parlamento/      ├── ide/          ├── educacion/
    ├── salud/           ├── mides/        ├── noticias/
    └── bps/
```

Cada módulo es independiente (`constants` · `schemas` · `client` · `tools` ·
`prompts`/`resources` opcionales). Importar el paquete registra automáticamente
todo lo que ofrece.

## 🛠️ Desarrollo

```bash
uv venv && uv pip install -e ".[dev]"

uv run pytest                  # 240 tests unitarios (HTTP mockeado, offline) · 89% cobertura
uv run pytest -m integration   # consulta las APIs de gobierno reales
uv run ruff check src tests
uv run pyright
```

## 🙌 Agradecimientos

Construido sobre datos publicados por **AGESIC**, **BCU**, **INE** y la
**Intendencia de Montevideo** en el marco de la ley de datos abiertos del Uruguay
(Nº 18.381). Este proyecto es un cliente independiente y no está afiliado a esas
instituciones.

## 📄 Licencia

[MIT](LICENSE)
