"""DuckDB connection helpers."""

from __future__ import annotations

from pathlib import Path

import duckdb


def connect_duckdb(db_path: Path) -> duckdb.DuckDBPyConnection:
    """Connect to a DuckDB database, creating parent directories when needed."""

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))
