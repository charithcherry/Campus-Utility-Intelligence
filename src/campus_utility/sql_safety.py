"""Read-only SQL safety helpers for the analytics copilot."""

from __future__ import annotations

import re
from pathlib import Path

import duckdb
import pandas as pd

BLOCKED_SQL_TOKENS = {
    "alter",
    "attach",
    "copy",
    "create",
    "delete",
    "detach",
    "drop",
    "export",
    "insert",
    "install",
    "load",
    "pragma",
    "truncate",
    "update",
}


def validate_readonly_select(sql: str, default_limit: int = 50) -> str:
    """Validate and normalize a single read-only SELECT statement."""

    normalized = " ".join(sql.strip().split())
    if not normalized:
        raise ValueError("SQL query is empty")
    if ";" in normalized:
        raise ValueError("Only one SQL statement is allowed")
    if not normalized.lower().startswith("select "):
        raise ValueError("Only SELECT statements are allowed")

    tokens = set(re.findall(r"[a-zA-Z_]+", normalized.lower()))
    blocked = sorted(tokens & BLOCKED_SQL_TOKENS)
    if blocked:
        raise ValueError(f"SQL query contains blocked token: {blocked[0]}")
    if not re.search(r"\blimit\b", normalized, flags=re.IGNORECASE):
        normalized = f"{normalized} LIMIT {default_limit}"
    return normalized


def execute_readonly_query(db_path: Path, sql: str, default_limit: int = 50) -> tuple[str, pd.DataFrame]:
    """Execute a safe read-only SQL query against DuckDB."""

    safe_sql = validate_readonly_select(sql, default_limit=default_limit)
    with duckdb.connect(str(db_path), read_only=True) as connection:
        return safe_sql, connection.execute(safe_sql).fetchdf()
