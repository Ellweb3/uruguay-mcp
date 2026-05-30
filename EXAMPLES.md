# Ejemplos de uso de uruguay_mcp

`uruguay_mcp` expone solo **5 meta-herramientas**. Todo dato concreto se alcanza a
través de ellas: primero `discover_tools` (o `plan_query`) para encontrar la
herramienta adecuada y su esquema, luego `call_tool` para ejecutarla, o
`execute_batch` para correr varias en paralelo.

Meta-tools:

- `list_modules()` — módulos disponibles y cuántas tools ofrece cada uno.
- `discover_tools(query, module=None, limit=8)` — busca tools por necesidad.
- `plan_query(goal)` — candidatos de varias fuentes para un objetivo amplio.
- `call_tool(name, arguments)` — ejecuta una tool por nombre.
- `execute_batch(calls)` — ejecuta `[{name, arguments}, ...]` en paralelo.

Módulos cargados por defecto: `catalogodatos`, `bcu`, `ine`, `gubuy`,
`montevideo`, `datastore` (31 data tools). Los nombres de tools usados abajo son
los reales registrados en cada módulo.

---

## 1. Cotización del dólar (BCU)

**Objetivo:** ¿A cuánto cerró el dólar en el último día hábil?

```text
discover_tools(query="cotización del dólar BCU", module="bcu")
  -> sugiere bcu_cotizacion_usd

call_tool("bcu_cotizacion_usd", {})
```

Sin `fecha`, usa el último cierre. Devuelve `compra` (TCC) y `venta` (TCV) del
dólar billete (moneda 2225) envueltos en el sobre estándar (`data`, `api`,
`url`, `cached`).

---

## 2. Serie de tipos de cambio en un rango (BCU)

**Objetivo:** Tipo de cambio del dólar y el real entre dos fechas.

```text
call_tool("bcu_listar_monedas", {"grupo": 2})
  -> tomar los códigos (ej. 2225 = dólar billete, 1001 = real)

call_tool("bcu_cotizaciones", {
  "monedas": [2225, 1001],
  "fecha_desde": "2025-01-02",
  "fecha_hasta": "2025-01-31",
  "grupo": 2
})
```

Primero `bcu_listar_monedas` para conocer los códigos numéricos, luego
`bcu_cotizaciones` con el rango. Devuelve una fila por moneda y fecha con
`compra`/`venta`/`arbitraje`.

---

## 3. Buscar y abrir un dataset del catálogo nacional (catalogodatos)

**Objetivo:** Encontrar datos abiertos sobre presupuesto público.

```text
discover_tools(query="datasets de presupuesto datos abiertos")
  -> catalogo_search_datasets

call_tool("catalogo_search_datasets", {"query": "presupuesto", "rows": 10})
  -> elegir un dataset y tomar su 'name'/'id'

call_tool("catalogo_get_dataset", {"id": "presupuesto-nacional"})
```

`catalogo_get_dataset` devuelve los `resources`; quedate con el `resource_id`
de uno que tenga datastore activo para el ejemplo 4.

---

## 4. Consultar registros tabulares de un recurso CKAN (catalogodatos)

**Objetivo:** Leer filas de un recurso con datastore, filtrando por texto.

```text
call_tool("catalogo_query_datastore", {
  "resource_id": "a1b2c3d4-0000-1111-2222-333344445555",
  "query": "Montevideo",
  "limit": 50,
  "offset": 0
})
```

`resource_id` sale del paso 3 (`catalogo_get_dataset`). Solo funciona sobre
recursos con datastore activo; si no lo tienen, descargá el archivo desde su
`url`.

---

## 5. Estudios estadísticos del INE (INE / ANDA)

**Objetivo:** Hallar el estudio del censo y abrir su ficha.

```text
discover_tools(query="censo de población INE", module="ine")
  -> ine_search_studies

call_tool("ine_search_studies", {
  "query": "censo", "rows": 10, "sort_by": "year", "sort_order": "desc"
})
  -> copiar el 'idno' ANDA (NO el id numérico)

call_tool("ine_get_study", {"idno": "URY-INE-CENSO-2023-v01"})
```

Ojo: `ine_get_study` requiere el `idno` (cadena ANDA), no el id numérico que
aparece en la búsqueda.

---

## 6. Datasets CKAN del INE

**Objetivo:** Listar los datasets de datos abiertos publicados por el INE.

```text
call_tool("ine_list_ckan_datasets", {"query": "precios", "rows": 20})
```

Devuelve los datasets CKAN del INE (complementa a los estudios ANDA del
ejemplo 5). Para leer las filas de uno de sus recursos, seguí con
`catalogo_query_datastore` usando el `resource_id` correspondiente.

---

## 7. Servicios y APIs de gub.uy (gubuy)

**Objetivo:** Ver qué servicios/APIs de gobierno existen sobre transporte.

```text
discover_tools(query="APIs de gobierno transporte gub.uy", module="gubuy")
  -> gubuy_search_apis, gubuy_list_servicios

execute_batch([
  {"name": "gubuy_search_apis",    "arguments": {"query": "transporte", "rows": 10}},
  {"name": "gubuy_list_servicios", "arguments": {"query": "transporte", "limit": 10}}
])
```

`execute_batch` corre ambas en paralelo con aislamiento de errores. Tomá un
`id`/`showcase_id` y profundizá con `gubuy_get_servicio` o
`gubuy_servicio_datasets`.

---

## 8. Próximo ómnibus en una parada (montevideo, transporte)

**Objetivo:** ¿Cuándo llega el 103 a una parada?

```text
discover_tools(query="cuándo llega el próximo bus a una parada", module="montevideo")
  -> montevideo_list_busstops, montevideo_busstop_lines, montevideo_bus_eta

call_tool("montevideo_list_busstops", {"query": "18 de Julio", "limit": 20})
  -> tomar el busstop_id

call_tool("montevideo_busstop_lines", {"busstop_id": 4567})
  -> confirmar qué líneas pasan

call_tool("montevideo_bus_eta", {"busstop_id": 4567, "lines": ["103"], "amount_per_line": 2})
```

`montevideo_bus_eta` exige `busstop_id` y al menos una línea. La unidad de
`eta` no está documentada (segundos o minutos): se devuelve sin transformar.

---

## 9. Buses cerca de un punto en tiempo real (montevideo, transporte)

**Objetivo:** Ver buses circulando cerca de una ubicación.

```text
call_tool("montevideo_buses_near", {
  "lat": -34.9011, "lng": -56.1645, "radius_m": 500
})
```

Devuelve posiciones GPS en tiempo real dentro del radio. Alternativa filtrada:
`montevideo_bus_positions` por `lines`, `company` o `busstop_id`.

---

## 10. CRUZADO — Transporte + multas de tránsito de Montevideo

**Objetivo:** Para un punto del centro, mostrar qué buses pasan cerca y, de
paso, el panorama de multas de tránsito (SUCIVE) de ese año.

```text
discover_tools(query="buses cerca y multas de tránsito Montevideo", module="montevideo")
  -> montevideo_buses_near, montevideo_multas_transito

execute_batch([
  {"name": "montevideo_buses_near",
   "arguments": {"lat": -34.9061, "lng": -56.1914, "radius_m": 400}},
  {"name": "montevideo_multas_transito",
   "arguments": {"year": 2018}}
])
```

Dos fuentes distintas dentro del mismo módulo, resueltas en paralelo:
tiempo real de transporte + el índice estadístico de multas. `multas_transito`
devuelve archivos anuales descargables y tablas de referencia (ordenanzas,
tipos de vehículo): son datos AGREGADOS, no una consulta de deuda por
matrícula.

---

## 11. CRUZADO — BCU + dataset del catálogo (tipo de cambio para contextualizar)

**Objetivo:** Cruzar la cotización oficial del dólar con un dataset de precios
o presupuesto del catálogo nacional para análisis monetario.

```text
plan_query(goal="contextualizar precios en pesos con el tipo de cambio del dólar")
  -> candidatos: bcu_cotizacion_usd, catalogo_search_datasets, catalogo_query_datastore

execute_batch([
  {"name": "bcu_cotizacion_usd",      "arguments": {}},
  {"name": "catalogo_search_datasets","arguments": {"query": "índice de precios", "rows": 5}}
])
  -> con un resource_id del resultado del catálogo:

call_tool("catalogo_query_datastore", {
  "resource_id": "ipc-0000-1111-2222-333344445555",
  "limit": 100
})
```

`plan_query` propone tools de **dos módulos** (`bcu` + `catalogodatos`). Se trae
el dólar y el dataset en paralelo con `execute_batch`, y luego se leen las filas
del recurso para convertir/contextualizar montos.

---

## 12. CRUZADO — Dos tablas CKAN para un JOIN lógico

**Objetivo:** Combinar dos recursos CKAN (uno del catálogo nacional, otro del
portal de Montevideo) para relacionar registros — un JOIN hecho del lado del
cliente con los resultados de dos datastores.

```text
discover_tools(query="consultar registros de un recurso CKAN", limit=8)
  -> catalogo_query_datastore, montevideo_query_datastore

# Tabla A: recurso del catálogo nacional
call_tool("catalogo_query_datastore", {
  "resource_id": "padron-organismos-0000-1111-2222-3333",
  "limit": 500
})

# Tabla B: recurso del portal de Montevideo
call_tool("montevideo_query_datastore", {
  "resource_id": "arbolado-publico-aaaa-bbbb-cccc-dddd",
  "limit": 500
})
```

Cada `*_query_datastore` devuelve registros de su portal CKAN respectivo;
el JOIN (por una clave común, ej. `organismo` o `barrio`) se arma combinando
los dos resultados. Para empujar el JOIN a un motor SQL real usá el módulo
`datastore` (cargado por defecto): `datastore_load_ckan_resource` para subir
cada recurso a una tabla SQLite y `datastore_sql` para el JOIN con SELECT.

---

## 13. Compra pública del Estado por OCDS (acce)

**Objetivo:** Listar las compras públicas más recientes publicadas por ACCE y
abrir el detalle estructurado de una de ellas (estándar OCDS: tender, awards,
items), sin autenticación.

```text
discover_tools(query="compras públicas recientes del Estado", limit=6)
  -> acce_recientes, acce_get_compra, acce_buscar

# Últimas compras publicadas (feed OCDS / RSS)
call_tool("acce_recientes", { "limit": 10 })
  -> lista de { id_compra, release_id, titulo, fecha }

# Detalle OCDS de una compra puntual
call_tool("acce_get_compra", { "id_compra": 1234567 })
  -> { tender (objeto, value, items[]), awards[], releases[] }
```

`acce_recientes` lee el RSS/feed OCDS y devuelve `id_compra` + `release_id`
para cada compra; pasá el `id_compra` a `acce_get_compra` para el `record` OCDS
completo (las `tender.value`/`award.value` pueden venir nulas y los `items` se
truncan a una muestra). Para buscar datasets de ACCE en el catálogo nacional
usá `acce_buscar`.

---

## 14. Buscar y leer una ley o decreto (impo)

**Objetivo:** Resolver una norma uruguaya (ley, decreto o la Constitución) a su
texto estructurado en IMPO, partiendo de una búsqueda en lenguaje natural.

```text
discover_tools(query="texto de una ley uruguaya por número y año", limit=6)
  -> impo_buscar_normativa, impo_get_norma, impo_diario_oficial

# Búsqueda: si trae tipo+número+año, resuelve directo a la norma
call_tool("impo_buscar_normativa", { "query": "ley 19210 inclusión financiera" })
  -> resuelve a impo_get_norma o devuelve URLs de búsqueda (degraded)

# Texto estructurado de una norma concreta
call_tool("impo_get_norma", {
  "tipo": "ley",
  "numero": 19210,
  "anio": 2014
})
  -> { titulo, metadata, articulos[] (con urlArticulo absoluto) }
```

`impo_get_norma` arma la ruta `/bases/{leyes|decretos|constitucion}/{n}-{año}`,
maneja el encoding latin-1 de IMPO, limpia el HTML embebido y devuelve los
artículos (capados por `max_articulos`). `version="original"` agrega
`-originales` (solo ley/decreto). Para el Diario Oficial de un día usá
`impo_diario_oficial` (devuelve las URLs canónicas de los PDF por sección).

---

## 15. Clima actual y alertas meteorológicas (inumet)

**Objetivo:** Obtener la última observación de las estaciones automáticas del
INUMET y verificar si hay advertencias/alertas vigentes.

```text
discover_tools(query="temperatura y viento actuales por estación", limit=6)
  -> inumet_estaciones, inumet_alertas, inumet_pronostico

# Última observación por estación automática (temp, humedad, viento, presión…)
call_tool("inumet_estaciones", { "station": "Carrasco", "limit": 5 })
  -> [{ estacion, temp, humedad, viento_kt, viento_kmh, presion, ... }]

# ¿Hay advertencia vigente?
call_tool("inumet_alertas", {})
  -> { activa, nivel (amarilla|naranja|roja), detalle, pdf_url }
```

`inumet_estaciones` consume el JSON `.mch` de las EMA y camina cada serie hacia
atrás hasta el último valor no nulo (el viento viene en nudos, con conversión a
km/h). `inumet_alertas` e `inumet_pronostico` scrapean HTML y degradan a
`status="partial"` si la página no parsea; `inumet_pronostico` da min/max y
descripción por período.

---

## Notas

- Toda respuesta de data tool viene en el sobre estándar: `data`, `api`, `url`,
  `cached` (y `error` ante fallos).
- `discover_tools` devuelve el esquema de argumentos de cada candidato: leelo
  antes de armar el `arguments` de `call_tool`.
- `execute_batch` aísla errores por llamada: una falla no aborta el resto.
- Los `resource_id` y `busstop_id` de los ejemplos son ilustrativos; obtenelos
  siempre del paso de búsqueda/listado previo.
