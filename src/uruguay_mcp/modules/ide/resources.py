"""Readable resources for the IDE Uruguay (datos espaciales) module."""

from __future__ import annotations

from ...shared.registry import resource
from .constants import GEO_BASE_URL, MODULE, WFS_URL


@resource(
    uri="uru://ide/guia-de-uso",
    name="Guía de uso de la IDE Uruguay (WFS + geocodificación)",
    description="Cómo descubrir capas, consultar features y geocodificar direcciones.",
    module=MODULE,
    mime_type="text/markdown",
)
def guia_de_uso() -> str:
    return (
        "# Guía de uso de la IDE Uruguay\n\n"
        "Infraestructura de Datos Espaciales de Uruguay (AGESIC). Dos superficies "
        "públicas sin autenticación:\n\n"
        f"- **WFS (GeoServer vectorial)**: {WFS_URL} — features geográficas "
        "(catastro, departamentos, calles, hidrografía...).\n"
        f"- **API de direcciones (AGESIC)**: {GEO_BASE_URL} — geocodificación "
        "directa e inversa (JSON plano con lat/lng en EPSG:4326).\n\n"
        "## Flujo recomendado\n\n"
        "1. **Descubrir capas** WFS con `ide_listar_capas` (filtro por subcadena, "
        "ej. 'catastro', 'limite', 'depart').\n"
        "2. **Consultar features** de una capa con `ide_features` (parámetro "
        "`capa`/typeNames). Para capas grandes pasá un `bbox` o un `cql_filter`. "
        "Usá `solo_conteo=true` para un conteo barato (resultType=hits).\n"
        "3. **Parcelas catastrales** con `ide_parcela_catastral` "
        "(tipo urbano/rural, departamento+padron o bbox).\n"
        "4. **Geocodificar una dirección** con `ide_geocodificar` "
        "(autocompletar=true para typeahead).\n"
        "5. **Geocodificación inversa** (lat/lon a dirección) con "
        "`ide_geocodificar_inverso`.\n\n"
        "## Notas\n\n"
        "- El WFS usa EPSG:4326; el `bbox` es 'miny,minx,maxy,maxx' "
        "(lat_min,lon_min,lat_max,lon_max) y se ensambla con la URI de CRS para "
        "evitar ambigüedad de ejes.\n"
        "- Las capas catastrales son enormes (~1M parcelas urbanas): siempre "
        "requieren bbox o filtro CQL.\n"
        "- Por defecto las geometrías se recortan a tipo + bbox + centroide; pedí "
        "`slim=false` solo si necesitás todas las coordenadas.\n"
        "- El `depto` del catastro es el NOMBRE del departamento en mayúsculas "
        "(ej. `depto='MONTEVIDEO'`), no un código numérico.\n"
        "- Para direcciones y números de puerta usá la API REST de direcciones, "
        "no el WFS (el workspace `direcciones` del WFS no es público).\n"
    )


@resource(
    uri="uru://ide/capas-destacadas",
    name="Capas destacadas de la IDE Uruguay",
    description="Listado orientativo de capas WFS de uso frecuente.",
    module=MODULE,
    mime_type="text/markdown",
)
def capas_destacadas() -> str:
    return (
        "# Capas destacadas de la IDE Uruguay\n\n"
        "Capas WFS de uso frecuente. Para el inventario exacto y actualizado usá "
        "la herramienta `ide_listar_capas` (cambia con el tiempo).\n\n"
        "## Catastro\n\n"
        "- `ET_CATASTRO:parcelario_urbano` — parcelas urbanas (~1M, requiere "
        "bbox/filtro).\n"
        "- `ET_CATASTRO:parcelario_rural` — parcelas rurales.\n"
        "- `ws_catastro:departamentos` — límites de los 19 departamentos.\n"
        "- `ws_catastro:localidades`, `ws_catastro:secciones`.\n\n"
        "## Límites administrativos y calles (workspace ideuy)\n\n"
        "- `ideuy:uyla_limite_departamental` — límites departamentales.\n"
        "- `ideuy:ejes_de_calle_ide_` — ejes de calle (centerlines).\n\n"
        "## Geocodificación de direcciones\n\n"
        "Para resolver direcciones a coordenadas usá la API REST con "
        "`ide_geocodificar` / `ide_geocodificar_inverso` (no el WFS).\n"
    )
