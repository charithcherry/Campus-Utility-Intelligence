"""Bronze ingestion for raw campus utility files."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb
from campus_utility.profiling import discover_raw_files


@dataclass(frozen=True)
class IngestedTable:
    """Metadata for one ingested bronze table."""

    source_path: Path
    table_name: str
    row_count: int
    column_count: int


def table_name_from_path(path: Path) -> str:
    """Return a stable bronze table name for a raw file path."""

    stem = re.sub(r"[^a-zA-Z0-9]+", "_", path.stem).strip("_").lower()
    if not stem:
        raise ValueError(f"Cannot derive table name from path: {path}")
    return f"bronze_{stem}"


def ingest_raw_files(raw_dir: Path, db_path: Path) -> list[IngestedTable]:
    """Load supported raw files into DuckDB bronze tables."""

    raw_files = discover_raw_files(raw_dir)
    if not raw_files:
        raise FileNotFoundError(f"No supported raw files found under {raw_dir}")

    ingested: list[IngestedTable] = []
    with connect_duckdb(db_path) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS bronze")
        for raw_file in raw_files:
            table_name = table_name_from_path(raw_file)
            qualified_name = f"bronze.{table_name}"
            source = str(raw_file)
            connection.execute(f"DROP TABLE IF EXISTS {qualified_name}")
            connection.execute(
                f"""
                CREATE TABLE {qualified_name} AS
                SELECT *
                FROM read_csv_auto(?, header = true, nullstr = ['N/A'], sample_size = -1)
                """,
                [source],
            )
            row_count = connection.execute(f"SELECT COUNT(*) FROM {qualified_name}").fetchone()[0]
            column_count = len(connection.execute(f"DESCRIBE {qualified_name}").fetchall())
            ingested.append(
                IngestedTable(
                    source_path=raw_file,
                    table_name=qualified_name,
                    row_count=int(row_count),
                    column_count=column_count,
                )
            )

    return ingested


def render_ingestion_summary(tables: list[IngestedTable], db_path: Path) -> str:
    """Render a short CLI summary for ingested tables."""

    lines = [f"Wrote bronze tables to {db_path}", f"Ingested tables: {len(tables)}"]
    for table in tables:
        lines.append(
            f"- {table.table_name}: {table.row_count} rows, "
            f"{table.column_count} columns from {table.source_path}"
        )
    return "\n".join(lines)


def write_ingestion_report(tables: list[IngestedTable], db_path: Path, output_path: Path) -> Path:
    """Write a markdown report for bronze ingestion results."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Bronze Ingestion Report",
        "",
        "## Purpose",
        "",
        "This report confirms that raw Kaggle UNICON files were loaded into DuckDB bronze tables.",
        "",
        "## What This Did",
        "",
        "- Loaded each supported raw file into the DuckDB `bronze` schema",
        "- Preserved raw source columns with minimal transformation",
        "- Recreated tables on each run so ingestion stays repeatable",
        "- Treated `N/A` values as null during CSV loading",
        "",
        "## Why This Matters",
        "",
        "Bronze makes the raw files queryable in SQL while keeping cleaning decisions out of the raw layer. Silver transformations use these bronze tables as their source.",
        "",
        f"DuckDB database: `{db_path}`",
        "",
        "| Source File | Bronze Table | Rows | Columns |",
        "| --- | --- | ---: | ---: |",
    ]
    for table in tables:
        lines.append(
            f"| `{table.source_path}` | `{table.table_name}` | "
            f"{table.row_count} | {table.column_count} |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for bronze ingestion."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Ingest raw campus utility files into DuckDB.")
    parser.add_argument("--raw-dir", type=Path, default=config.raw_dir)
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument("--report-path", type=Path, default=Path("reports/bronze_ingestion_report.md"))
    args = parser.parse_args()

    tables = ingest_raw_files(args.raw_dir, args.db_path)
    print(render_ingestion_summary(tables, args.db_path))
    report_path = write_ingestion_report(tables, args.db_path, args.report_path)
    print(f"Wrote ingestion report to {report_path}")


if __name__ == "__main__":
    main()
