"""Local SQLite store and source ingestion for the datastore module.

A single SQLite connection is kept open for the lifetime of the process so that
``:memory:`` tables persist across tool calls. All ingestion goes through
:func:`load_rows`, which sanitizes the table name and creates an all-TEXT table
(SQLite is dynamically typed, so values keep their original string form and the
model can CAST as needed in SQL).
"""

from __future__ import annotations

import csv
import io
import re
import sqlite3
import threading
from typing import Any

from ...shared import errors, http
from .constants import (
    API_NAME,
    CKAN_PAGE,
    DB_PATH,
    MAX_RESULT_ROWS,
    MAX_ROWS,
    SQL_TIMEOUT,
)

_conn: sqlite3.Connection | None = None
_lock = threading.Lock()

_IDENT_RE = re.compile(r"[^0-9a-zA-Z_]")


def get_conn() -> sqlite3.Connection:
    """Return the process-wide SQLite connection, creating it on first use."""
    global _conn
    with _lock:
        if _conn is None:
            _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            _conn.row_factory = sqlite3.Row
        return _conn


def reset() -> None:
    """Drop the connection (used by tests to isolate state)."""
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
        _conn = None


def sanitize_identifier(name: str) -> str:
    """Turn an arbitrary string into a safe SQL identifier.

    Non-alphanumeric characters become underscores; a leading digit is prefixed
    with ``t_``. Raises :class:`ValidationError` when nothing usable remains.
    """
    cleaned = _IDENT_RE.sub("_", (name or "").strip())
    cleaned = cleaned.strip("_")
    if not cleaned:
        raise errors.ValidationError("nombre de tabla inválido")
    if cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"
    return cleaned[:64]


def load_rows(table: str, columns: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    """Create (or replace) ``table`` with the given columns and rows.

    All columns are stored as TEXT. Returns a small summary dict.
    """
    safe_table = sanitize_identifier(table)
    safe_cols = [sanitize_identifier(c) or f"c_{i}" for i, c in enumerate(columns)]
    if not safe_cols:
        raise errors.ValidationError("la fuente no tiene columnas")
    # De-duplicate column names while preserving order.
    seen: dict[str, int] = {}
    final_cols: list[str] = []
    for col in safe_cols:
        if col in seen:
            seen[col] += 1
            final_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            final_cols.append(col)

    conn = get_conn()
    col_defs = ", ".join(f'"{c}" TEXT' for c in final_cols)
    placeholders = ", ".join("?" for _ in final_cols)
    with _lock, conn:
        conn.execute(f'DROP TABLE IF EXISTS "{safe_table}"')
        conn.execute(f'CREATE TABLE "{safe_table}" ({col_defs})')
        width = len(final_cols)
        # Normalize each row to the table width (pad/truncate) and stringify.
        norm = [
            [None if v is None else str(v) for v in (r[:width] + [None] * (width - len(r)))]
            for r in rows
        ]
        conn.executemany(
            f'INSERT INTO "{safe_table}" VALUES ({placeholders})', norm
        )
    return {"table": safe_table, "columns": final_cols, "rows_loaded": len(rows)}


async def fetch_text(url: str) -> str:
    """Download ``url`` and return its body as text, raising on failure."""
    try:
        resp = await http._request("GET", url, api=API_NAME)
    except Exception as exc:  # noqa: BLE001 — normalized below
        raise errors.upstream(API_NAME, str(exc)) from exc
    if resp.status_code >= 400:
        raise errors.upstream(API_NAME, f"HTTP {resp.status_code}", status=resp.status_code)
    return resp.text


def parse_csv(text: str, max_rows: int = MAX_ROWS) -> tuple[list[str], list[list[str]]]:
    """Parse CSV text into (header, rows), capping at ``max_rows`` data rows."""
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise errors.ValidationError("el CSV está vacío") from exc
    rows: list[list[str]] = []
    for i, row in enumerate(reader):
        if i >= max_rows:
            break
        rows.append(row)
    return header, rows


async def load_csv_url(url: str, table: str, max_rows: int) -> dict[str, Any]:
    text = await fetch_text(url)
    header, rows = parse_csv(text, max_rows=max_rows)
    summary = load_rows(table, header, rows)
    summary["source_url"] = url
    return summary


async def load_ckan_resource(
    resource_id: str, table: str, base: str, max_rows: int
) -> dict[str, Any]:
    """Load a CKAN resource into a table via the datastore_search API.

    Pages through ``datastore_search`` until ``max_rows`` (or the end) is hit.
    """
    action = f"{base.rstrip('/')}/api/3/action/datastore_search"
    fields: list[str] = []
    records: list[dict[str, Any]] = []
    offset = 0
    while len(records) < max_rows:
        limit = min(CKAN_PAGE, max_rows - len(records))
        params = {"resource_id": resource_id, "limit": limit, "offset": offset}
        payload = await http.get_json(action, api=API_NAME, params=params)
        if not isinstance(payload, dict) or not payload.get("success"):
            detail = (payload or {}).get("error", "respuesta inválida")
            raise errors.upstream(API_NAME, str(detail))
        result = payload.get("result") or {}
        if not fields:
            fields = [f.get("id") for f in result.get("fields", []) if f.get("id") != "_id"]
        page = result.get("records", [])
        if not page:
            break
        records.extend(page)
        offset += len(page)
        if len(page) < limit:
            break

    if not fields and records:
        fields = [k for k in records[0] if k != "_id"]
    rows = [[rec.get(f) for f in fields] for rec in records[:max_rows]]
    summary = load_rows(table, fields, rows)
    summary["source_url"] = action
    summary["resource_id"] = resource_id
    return summary


_SELECT_RE = re.compile(r"^\s*select\b", re.IGNORECASE)
_FORBIDDEN_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|"
    r"vacuum|reindex|truncate|begin|commit|rollback)\b",
    re.IGNORECASE,
)


def assert_read_only(query: str) -> str:
    """Validate that ``query`` is a single read-only SELECT, or raise.

    Rejects multiple statements, anything that isn't a SELECT, and any forbidden
    keyword (DDL/DML/PRAGMA/ATTACH, etc.).
    """
    stripped = (query or "").strip().rstrip(";").strip()
    if not stripped:
        raise errors.ValidationError("la consulta está vacía")
    if ";" in stripped:
        raise errors.ValidationError("sólo se permite una única sentencia SELECT")
    if not _SELECT_RE.match(stripped):
        raise errors.ValidationError("sólo se permiten consultas SELECT")
    if _FORBIDDEN_RE.search(stripped):
        raise errors.ValidationError("la consulta contiene operaciones no permitidas")
    return stripped


def run_select(query: str) -> dict[str, Any]:
    """Execute a validated SELECT and return columns + capped rows."""
    sql = assert_read_only(query)
    conn = get_conn()
    conn.execute("PRAGMA query_only = ON")  # belt-and-suspenders read-only guard
    # Abort runaway queries via a statement progress handler timeout.
    deadline = {"hits": 0}
    max_steps = int(SQL_TIMEOUT * 1_000_000)

    def _guard() -> int:
        deadline["hits"] += 1
        return 1 if deadline["hits"] > max_steps else 0

    conn.set_progress_handler(_guard, 1_000_000)
    try:
        with _lock:
            cur = conn.execute(sql)
            columns = [d[0] for d in cur.description] if cur.description else []
            fetched = cur.fetchmany(MAX_RESULT_ROWS + 1)
    except sqlite3.Error as exc:
        raise errors.ValidationError(f"error SQL: {exc}") from exc
    finally:
        conn.set_progress_handler(None, 0)

    truncated = len(fetched) > MAX_RESULT_ROWS
    rows = [list(r) for r in fetched[:MAX_RESULT_ROWS]]
    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
    }


def list_tables() -> list[dict[str, Any]]:
    """Return loaded tables with their row counts and column names."""
    conn = get_conn()
    with _lock:
        names = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        out: list[dict[str, Any]] = []
        for name in names:
            count = conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{name}")').fetchall()]
            out.append({"table": name, "row_count": count, "columns": cols})
    return out
