"""Run reusable SQL analytics queries."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb


@dataclass(frozen=True)
class QueryResult:
    """Result metadata for one analytics query."""

    query_name: str
    row_count: int
    output_path: Path


def run_analytics_queries(db_path: Path, query_dir: Path, output_dir: Path) -> list[QueryResult]:
    """Run SQL files and write each result as markdown."""

    sql_files = sorted(query_dir.glob("*.sql"))
    if not sql_files:
        raise FileNotFoundError(f"No SQL files found in {query_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[QueryResult] = []
    with connect_duckdb(db_path) as connection:
        for sql_file in sql_files:
            query = sql_file.read_text(encoding="utf-8")
            rows = connection.execute(query).fetchall()
            columns = [description[0] for description in connection.description]
            output_path = output_dir / f"{sql_file.stem}.md"
            output_path.write_text(
                render_query_result(sql_file.stem, query, columns, rows),
                encoding="utf-8",
            )
            results.append(
                QueryResult(query_name=sql_file.stem, row_count=len(rows), output_path=output_path)
            )
    return results


def render_query_result(
    query_name: str,
    query: str,
    columns: list[str],
    rows: list[tuple[object, ...]],
) -> str:
    """Render a query result as markdown."""

    lines = [
        f"# Analytics Query: {query_name}",
        "",
        "## Purpose",
        "",
        "This output captures a reusable SQL analysis result from the DuckDB warehouse.",
        "",
        "## SQL",
        "",
        "```sql",
        query.strip(),
        "```",
        "",
        "## Result",
        "",
    ]
    lines.extend(_markdown_table(columns, rows))
    return "\n".join(lines) + "\n"


def _markdown_table(columns: list[str], rows: list[tuple[object, ...]]) -> list[str]:
    if not columns:
        return ["No columns returned."]

    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_format_value(value) for value in row) + " |")
    return lines


def _format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_analytics_summary(results: list[QueryResult], output_dir: Path) -> str:
    """Render a CLI summary."""

    lines = [f"Wrote analytics query outputs to {output_dir}", f"Queries run: {len(results)}"]
    for result in results:
        lines.append(f"- {result.query_name}: {result.row_count} rows")
    return "\n".join(lines)


def write_analytics_report(results: list[QueryResult], output_path: Path) -> Path:
    """Write an index report for analytics query outputs."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SQL Analytics Report",
        "",
        "## Purpose",
        "",
        "This report indexes reusable SQL analytics outputs for usage, peak demand, and estimated emissions.",
        "",
        "## Why This Matters",
        "",
        "These queries prove the warehouse can answer practical facility energy questions without relying on a dashboard yet.",
        "",
        "| Query | Rows | Output |",
        "| --- | ---: | --- |",
    ]
    for result in results:
        lines.append(f"| `{result.query_name}` | {result.row_count} | `{result.output_path}` |")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for SQL analytics."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Run reusable SQL analytics queries.")
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument("--query-dir", type=Path, default=Path("sql/marts"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/sql_analytics"))
    parser.add_argument("--report-path", type=Path, default=Path("reports/sql_analytics_report.md"))
    args = parser.parse_args()

    results = run_analytics_queries(args.db_path, args.query_dir, args.output_dir)
    print(render_analytics_summary(results, args.output_dir))
    report_path = write_analytics_report(results, args.report_path)
    print(f"Wrote analytics report to {report_path}")


if __name__ == "__main__":
    main()
