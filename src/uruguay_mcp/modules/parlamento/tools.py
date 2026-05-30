"""Discoverable tools for the Parlamento del Uruguay (CKAN, org-scoped)."""

from __future__ import annotations

import re
from typing import Any

from ...shared import errors
from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import CKAN_API_NAME, MODULE, ORG_SLUG
from .schemas import ActividadesArgs, AsistenciasArgs, BuscarArgs, GetDatasetArgs

# Slugs of the datasets backing the convenience tools (asistencias/actividades).
# Per cámara so a single tool can resolve the right dataset + legislatura.
_ASISTENCIAS_SLUG = {
    "representantes": "parlamento-del-uruguay-asistencias-a-la-camara-de-representantes",
    "senadores": "parlamento-del-uruguay-asistencias-a-la-camara-de-senadores",
}
_ACTIVIDADES_SLUG = {
    "senado": "parlamento-del-uruguay-actividades-del-senado",
    "representantes": "parlamento-del-uruguay-actividades-de-la-camara-de-representantes",
}

_LEG_RE = re.compile(r"(\d{2,3})")


def _slim_dataset(pkg: dict[str, Any]) -> dict[str, Any]:
    """Project a CKAN package down to the fields a model actually needs."""
    return {
        "id": pkg.get("id"),
        "name": pkg.get("name"),
        "title": pkg.get("title"),
        "notes": pkg.get("notes"),
        "organization": (pkg.get("organization") or {}).get("title"),
        "num_resources": pkg.get("num_resources"),
        "metadata_modified": pkg.get("metadata_modified"),
        "resources": [_slim_resource(r) for r in pkg.get("resources", [])],
    }


def _slim_resource(r: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": r.get("id"),
        "name": r.get("name"),
        "format": r.get("format"),
        "url": r.get("url"),
        "datastore_active": r.get("datastore_active", False),
    }


def _resource_legislatura(resource: dict[str, Any]) -> int | None:
    """Extract the legislatura number from a resource name (e.g. '... Leg 49')."""
    name = (resource.get("name") or "")
    if "metadato" in name.lower():
        return None
    nums = [int(m.group()) for m in _LEG_RE.finditer(name)]
    # Legislatura numbers are 2-3 digits in a plausible range; pick the last.
    nums = [n for n in nums if 30 <= n <= 120]
    return nums[-1] if nums else None


def _pick_resource(
    resources: list[dict[str, Any]], legislatura: int | None
) -> dict[str, Any] | None:
    """Choose the datastore-active resource for a legislatura (or the newest)."""
    active = [r for r in resources if r.get("datastore_active")]
    if not active:
        return None
    if legislatura is not None:
        for r in active:
            if _resource_legislatura(r) == legislatura:
                return r
        return None
    # Default: the most recent legislatura among active resources.
    def _key(r: dict[str, Any]) -> int:
        return _resource_legislatura(r) or -1

    return max(active, key=_key)


@tool(
    name="parlamento_buscar",
    module=MODULE,
    summary=(
        "Buscar datasets del Parlamento del Uruguay (Cámara de Representantes y "
        "Senado) en el Catálogo Nacional. Inyecta fq=organization:parlamento-uruguayo "
        "automáticamente. Cubre asistencias, actividades, pedidos de informes, "
        "leyes, comisiones, proyectos y más."
    ),
    params_model=BuscarArgs,
    keywords=[
        "parlamento", "diputados", "senadores", "legislativo", "buscar", "dataset",
        "camara", "asistencias", "pedidos de informes", "leyes",
    ],
)
async def buscar(query: str = "", rows: int = 20, start: int = 0) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": query or "*:*",
        "fq": f"organization:{ORG_SLUG}",
        "rows": rows,
        "start": start,
    }
    result, cached, url = await client.package_search(params)
    return envelope(
        {
            "count": result.get("count"),
            "results": [_slim_dataset(p) for p in result.get("results", [])],
        },
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="parlamento_get_dataset",
    module=MODULE,
    summary=(
        "Obtener metadatos completos y recursos (con resource_id, formato y "
        "datastore_active) de un dataset del Parlamento por slug o uuid. Los "
        "recursos suelen estar divididos por legislatura."
    ),
    params_model=GetDatasetArgs,
    keywords=[
        "parlamento", "dataset", "recursos", "detalle", "metadatos", "legislatura",
        "resource_id",
    ],
)
async def get_dataset(id: str) -> dict[str, Any]:
    result, cached, url = await client.package_show(id)
    return envelope(_slim_dataset(result), api=CKAN_API_NAME, url=url, cached=cached)


async def _query_camara_dataset(
    slug: str,
    legislatura: int | None,
    query: str | None,
    limit: int,
    offset: int,
    *,
    no_active_msg: str,
    no_leg_msg: str,
) -> dict[str, Any]:
    """Resolve a dataset's datastore-active resource and query its rows."""
    pkg, _, _ = await client.package_show(slug)
    resources = pkg.get("resources", [])
    resource = _pick_resource(resources, legislatura)
    if resource is None:
        msg = no_leg_msg if legislatura is not None else no_active_msg
        raise errors.NotFoundError(msg, details={"dataset": slug, "legislatura": legislatura})

    params: dict[str, Any] = {
        "resource_id": resource["id"],
        "limit": limit,
        "offset": offset,
    }
    if query:
        params["q"] = query
    result, cached, url = await client.datastore_search(params)
    return envelope(
        {
            "dataset": pkg.get("name"),
            "legislatura": _resource_legislatura(resource),
            "resource_id": resource["id"],
            "resource_name": resource.get("name"),
            "total": result.get("total"),
            "fields": result.get("fields"),
            "records": result.get("records"),
        },
        api=CKAN_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="parlamento_asistencias",
    module=MODULE,
    summary=(
        "Asistencias a sesiones de la Cámara (Diputados o Senadores) por "
        "legislatura. Resuelve el resource_id datastore-activo del dataset de "
        "asistencias y consulta sus registros. NOTA: la copia CKAN expone filas a "
        "NIVEL SESIÓN (Fecha, Asunto, Carpetas, Título), NO el presentismo "
        "por legislador. Para asistencia individual (Nombre, Citaciones, "
        "Asistencias %) hay que ir a la fuente directa de parlamento.gub.uy."
    ),
    params_model=AsistenciasArgs,
    keywords=[
        "asistencias", "presentismo", "faltas", "diputados", "senadores", "sesiones",
        "legislatura", "parlamento",
    ],
)
async def asistencias(
    camara: str = "representantes",
    legislatura: int | None = None,
    query: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    slug = _ASISTENCIAS_SLUG.get(camara.lower())
    if slug is None:
        raise errors.ValidationError(
            "Cámara inválida: usá 'representantes' o 'senadores'.",
            details={"camara": camara},
        )
    return await _query_camara_dataset(
        slug,
        legislatura,
        query,
        limit,
        offset,
        no_active_msg="No hay recursos con datastore activo para asistencias.",
        no_leg_msg=(
            "No se encontró un recurso consultable para esa legislatura; "
            "usá parlamento_get_dataset para ver las legislaturas disponibles."
        ),
    )


@tool(
    name="parlamento_actividades",
    module=MODULE,
    summary=(
        "Actividades/citaciones de la Cámara (Diputados o Senado): plenarios y "
        "comisiones por legislatura. Resuelve el recurso datastore-activo y "
        "consulta sus filas (Cuerpo, Comisión, FechaHora, Actividad, Sala)."
    ),
    params_model=ActividadesArgs,
    keywords=[
        "actividades", "citaciones", "agenda", "comisiones", "plenario", "senado",
        "diputados", "sesiones", "parlamento",
    ],
)
async def actividades(
    camara: str = "senado",
    legislatura: int | None = None,
    query: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    slug = _ACTIVIDADES_SLUG.get(camara.lower())
    if slug is None:
        raise errors.ValidationError(
            "Cámara inválida: usá 'senado' o 'representantes'.",
            details={"camara": camara},
        )
    return await _query_camara_dataset(
        slug,
        legislatura,
        query,
        limit,
        offset,
        no_active_msg="No hay recursos con datastore activo para actividades.",
        no_leg_msg=(
            "No se encontró un recurso consultable para esa legislatura; "
            "usá parlamento_get_dataset para ver las legislaturas disponibles."
        ),
    )
