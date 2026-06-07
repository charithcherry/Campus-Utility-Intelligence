"""Estimated electricity emissions metrics."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb


@dataclass(frozen=True)
class EmissionsTable:
    """Metadata for the emissions metric table."""

    table_name: str
    row_count: int
    emissions_factor: float


def build_emissions_metrics(db_path: Path, emissions_factor: float) -> EmissionsTable:
    """Build estimated monthly electricity emissions from gold monthly usage."""

    with connect_duckdb(db_path) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
        connection.execute("DROP TABLE IF EXISTS gold.gold_electricity_emissions")
        connection.execute(
            """
            CREATE TABLE gold.gold_electricity_emissions AS
            SELECT
                campus_id,
                source_system,
                usage_month,
                total_consumption,
                ?::DOUBLE AS emissions_factor_kg_co2e_per_unit,
                total_consumption * ?::DOUBLE AS estimated_emissions_kg_co2e
            FROM gold.gold_monthly_electricity_usage
            """,
            [emissions_factor, emissions_factor],
        )
        row_count = connection.execute(
            "SELECT COUNT(*) FROM gold.gold_electricity_emissions"
        ).fetchone()[0]

    return EmissionsTable(
        table_name="gold.gold_electricity_emissions",
        row_count=int(row_count),
        emissions_factor=emissions_factor,
    )


def render_emissions_summary(table: EmissionsTable, db_path: Path) -> str:
    """Render a short CLI summary."""

    return (
        f"Wrote emissions metrics to {db_path}\n"
        f"- {table.table_name}: {table.row_count} rows using factor "
        f"{table.emissions_factor} kg CO2e per usage unit"
    )


def write_emissions_report(table: EmissionsTable, db_path: Path, output_path: Path) -> Path:
    """Write a markdown report for estimated emissions."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Emissions Metrics Report",
        "",
        "## Purpose",
        "",
        "This report confirms that monthly electricity usage was converted into estimated emissions.",
        "",
        "## What This Built",
        "",
        "- `gold.gold_electricity_emissions`",
        "- Estimated emissions by campus, source, and month",
        "- A documented emissions factor on every row",
        "",
        "## Why This Matters",
        "",
        "This gives a sustainability estimate that can be reviewed, replaced with an official factor, and used in later dashboard views.",
        "",
        "## Assumption",
        "",
        f"The emissions factor is `{table.emissions_factor}` kg CO2e per usage unit. It is configurable and should be replaced if a more specific official factor is required.",
        "",
        f"DuckDB database: `{db_path}`",
        "",
        "| Gold Table | Rows |",
        "| --- | ---: |",
        f"| `{table.table_name}` | {table.row_count} |",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for emissions metrics."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Build estimated electricity emissions metrics.")
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument(
        "--emissions-factor",
        type=float,
        default=config.electricity_emissions_factor_kg_co2e_per_unit,
    )
    parser.add_argument("--report-path", type=Path, default=Path("reports/emissions_metrics_report.md"))
    args = parser.parse_args()

    table = build_emissions_metrics(args.db_path, args.emissions_factor)
    print(render_emissions_summary(table, args.db_path))
    report_path = write_emissions_report(table, args.db_path, args.report_path)
    print(f"Wrote emissions report to {report_path}")


if __name__ == "__main__":
    main()
