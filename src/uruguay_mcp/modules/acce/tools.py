"""Discoverable tools for ACCE (compras estatales / OCDS + CKAN)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from ...shared.envelope import envelope
from ...shared.registry import tool
from . import client
from .constants import (
    CKAN_API_NAME,
    CKAN_ORG,
    MAX_ITEMS,
    MODULE,
    OCDS_API_NAME,
)
from .schemas import BuscarArgs, CompraArgs, RecientesArgs, ReleaseArgs

# id_compra and release_id are packed into each RSS <title>.
_TITLE_RE = re.compile(r"id_compra:(\d+),release_id:(.+)")


def _parse_rss(xml_text: str) -> list[dict[str, Any]]:
    """Project RSS items down to the fields a model needs."""
    root = ET.fromstring(xml_text)
    items: list[dict[str, Any]] = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        id_compra: str | None = None
        release_id: str | None = guid or None
        m = _TITLE_RE.search(title)
        if m:
            id_compra = m.group(1)
            release_id = release_id or m.group(2).strip()
        items.append(
            {
                "id_compra": id_compra,
                "release_id": release_id,
                "tag": (item.findtext("category") or "").strip() or None,
                "title": title or None,
                "date": (item.findtext("pubDate") or "").strip() or None,
                "link": (item.findtext("link") or "").strip() or None,
            }
        )
    return items


def _slim_party(party: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": party.get("id"),
        "name": party.get("name"),
        "roles": party.get("roles", []),
    }


def _slim_items(items: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Cap a possibly-huge items list to a count plus the first N entries."""
    items = items or []
    sample = [
        {
            "id": it.get("id"),
            "description": it.get("description"),
            "classification": (it.get("classification") or {}).get("description"),
            "quantity": it.get("quantity"),
            "unit": (it.get("unit") or {}).get("name"),
        }
        for it in items[:MAX_ITEMS]
    ]
    return {"count": len(items), "sample": sample}


def _slim_tender(tender: dict[str, Any]) -> dict[str, Any]:
    value = tender.get("value") or {}
    period = tender.get("tenderPeriod") or {}
    return {
        "id": tender.get("id"),
        "title": tender.get("title"),
        "description": tender.get("description"),
        "status": tender.get("status"),
        "procurementMethod": tender.get("procurementMethod"),
        "procurementMethodDetails": tender.get("procurementMethodDetails"),
        "procuringEntity": (tender.get("procuringEntity") or {}).get("name"),
        "value": value.get("amount"),
        "currency": value.get("currency"),
        "tenderPeriod": {"start": period.get("startDate"), "end": period.get("endDate")},
        "items": _slim_items(tender.get("items")),
    }


def _slim_award(award: dict[str, Any]) -> dict[str, Any]:
    value = award.get("value") or {}
    return {
        "id": award.get("id"),
        "status": award.get("status"),
        "date": award.get("date"),
        "suppliers": [
            {"id": s.get("id"), "name": s.get("name")} for s in award.get("suppliers", [])
        ],
        "value": value.get("amount"),
        "currency": value.get("currency"),
        "items": _slim_items(award.get("items")),
    }


def _slim_release(rel: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ocid": rel.get("ocid"),
        "id": rel.get("id"),
        "date": rel.get("date"),
        "tag": rel.get("tag", []),
        "initiationType": rel.get("initiationType"),
        "buyer": (rel.get("buyer") or {}).get("name"),
        "parties": [_slim_party(p) for p in rel.get("parties", [])],
    }
    tender = rel.get("tender") or {}
    if tender:
        out["tender"] = _slim_tender(tender)
    awards = rel.get("awards") or []
    if awards:
        out["awards"] = [_slim_award(a) for a in awards]
    return out


def _slim_dataset(pkg: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": pkg.get("id"),
        "name": pkg.get("name"),
        "title": pkg.get("title"),
        "notes": pkg.get("notes"),
        "organization": (pkg.get("organization") or {}).get("title"),
        "tags": [t.get("name") for t in pkg.get("tags", [])],
        "num_resources": pkg.get("num_resources"),
        "metadata_modified": pkg.get("metadata_modified"),
        "resources": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "format": r.get("format"),
                "url": r.get("url"),
                "datastore_active": r.get("datastore_active", False),
            }
            for r in pkg.get("resources", [])
        ],
    }


@tool(
    name="acce_recientes",
    module=MODULE,
    summary=(
        "Listar las compras/contrataciones públicas más recientes (releases OCDS) "
        "desde el feed RSS de ACCE: id_compra, release_id, tipo (tag), título y fecha."
    ),
    params_model=RecientesArgs,
    keywords=[
        "compras",
        "estatales",
        "licitaciones",
        "recientes",
        "ocds",
        "acce",
        "contrataciones",
        "rss",
        "adjudicaciones",
    ],
)
async def recientes(
    year: int | None = None,
    month: int | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    xml_text, cached, url = await client.fetch_rss(year, month)
    items = _parse_rss(xml_text)
    if tag:
        items = [it for it in items if (it.get("tag") or "").lower() == tag.lower()]
    items = items[:limit]
    return envelope(
        {"count": len(items), "results": items},
        api=OCDS_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="acce_get_compra",
    module=MODULE,
    summary=(
        "Obtener el record OCDS de una compra por id_compra: ocid y lista de "
        "eventos/etapas enlazados (release_id, tag, fecha). Use acce_get_release "
        "para el detalle de cada evento."
    ),
    params_model=CompraArgs,
    keywords=[
        "compra",
        "record",
        "ocds",
        "expediente",
        "etapas",
        "ocid",
        "acce",
        "idcompra",
    ],
)
async def get_compra(idcompra: str) -> dict[str, Any]:
    result, cached, url = await client.get_record(idcompra)
    records = (result or {}).get("records", []) if isinstance(result, dict) else []
    record = records[0] if records else {}
    events = []
    for rel in record.get("releases", []):
        link = rel.get("url", "")
        release_id = link.rsplit("/", 1)[-1] if link else None
        events.append(
            {
                "release_id": release_id,
                "url": link or None,
                "date": rel.get("date"),
                "tag": rel.get("tag", []),
            }
        )
    return envelope(
        {
            "ocid": record.get("ocid"),
            "idcompra": idcompra,
            "publishedDate": (result or {}).get("publishedDate"),
            "events": events,
        },
        api=OCDS_API_NAME,
        url=url,
        cached=cached,
    )


@tool(
    name="acce_get_release",
    module=MODULE,
    summary=(
        "Obtener el detalle completo de un evento OCDS (release) por release_id: "
        "para llamados, datos del tender; para adjudicaciones, los awards "
        "(proveedor, ítems, valor si existe). Campos esenciales ya recortados."
    ),
    params_model=ReleaseArgs,
    keywords=[
        "release",
        "detalle",
        "licitacion",
        "adjudicacion",
        "tender",
        "award",
        "proveedor",
        "ocds",
        "acce",
        "items",
    ],
)
async def get_release(param: str) -> dict[str, Any]:
    result, cached, url = await client.get_release(param)
    releases = (result or {}).get("releases", []) if isinstance(result, dict) else []
    data = _slim_release(releases[0]) if releases else {"releases": []}
    return envelope(data, api=OCDS_API_NAME, url=url, cached=cached)


@tool(
    name="acce_buscar",
    module=MODULE,
    summary=(
        "Buscar datasets de la Agencia Reguladora de Compras Estatales (ACCE) en el "
        "Catálogo Nacional de Datos Abiertos (CKAN): RUPE, datos históricos de "
        "compras, etc. Fuerza fq=organization:acce."
    ),
    params_model=BuscarArgs,
    keywords=[
        "acce",
        "datasets",
        "rupe",
        "proveedores",
        "ckan",
        "datos abiertos",
        "compras historicas",
        "buscar",
    ],
)
async def buscar(query: str = "", rows: int = 20, start: int = 0) -> dict[str, Any]:
    params: dict[str, Any] = {
        "q": query or "*:*",
        "fq": f"organization:{CKAN_ORG}",
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
