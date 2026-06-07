"""Campus-level NMI versus building usage reconciliation."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb


@dataclass(frozen=True)
class ReconciliationTable:
    """Metadata for one reconciliation table."""

    table_name: str
    row_count: int
    description: str


def build_reconciliation_tables(db_path: Path) -> list[ReconciliationTable]:
    """Create campus-level NMI versus building usage reconciliation tables."""

    with connect_duckdb(db_path) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
        _create_daily_reconciliation(connection)
        _create_monthly_reconciliation(connection)

        return [
            _table_result(
                connection,
                "gold.gold_daily_nmi_building_reconciliation",
                "Daily campus-level NMI usage compared with summed building usage.",
            ),
            _table_result(
                connection,
                "gold.gold_monthly_nmi_building_reconciliation",
                "Monthly campus-level NMI usage compared with summed building usage.",
            ),
        ]


def _create_daily_reconciliation(connection) -> None:
    connection.execute("DROP TABLE IF EXISTS gold.gold_daily_nmi_building_reconciliation")
    connection.execute(
        """
        CREATE TABLE gold.gold_daily_nmi_building_reconciliation AS
        WITH nmi AS (
            SELECT
                campus_id,
                usage_date,
                SUM(total_consumption) AS nmi_consumption
            FROM gold.gold_daily_electricity_usage
            WHERE source_system = 'nmi_consumption'
            GROUP BY campus_id, usage_date
        ),
        building AS (
            SELECT
                campus_id,
                usage_date,
                SUM(total_consumption) AS building_consumption
            FROM gold.gold_daily_electricity_usage
            WHERE source_system = 'building_consumption'
            GROUP BY campus_id, usage_date
        )
        SELECT
            COALESCE(nmi.campus_id, building.campus_id) AS campus_id,
            COALESCE(nmi.usage_date, building.usage_date) AS usage_date,
            nmi.nmi_consumption,
            building.building_consumption,
            nmi.nmi_consumption - building.building_consumption AS consumption_difference,
            CASE
                WHEN nmi.nmi_consumption IS NULL THEN NULL
                WHEN nmi.nmi_consumption = 0 THEN NULL
                ELSE (nmi.nmi_consumption - building.building_consumption) / nmi.nmi_consumption
            END AS difference_ratio_to_nmi
        FROM nmi
        FULL OUTER JOIN building
          ON nmi.campus_id = building.campus_id
         AND nmi.usage_date = building.usage_date
        """
    )


def _create_monthly_reconciliation(connection) -> None:
    connection.execute("DROP TABLE IF EXISTS gold.gold_monthly_nmi_building_reconciliation")
    connection.execute(
        """
        CREATE TABLE gold.gold_monthly_nmi_building_reconciliation AS
        SELECT
            campus_id,
            DATE_TRUNC('month', usage_date)::DATE AS usage_month,
            SUM(nmi_consumption) AS nmi_consumption,
            SUM(building_consumption) AS building_consumption,
            SUM(nmi_consumption) - SUM(building_consumption) AS consumption_difference,
            CASE
                WHEN SUM(nmi_consumption) IS NULL THEN NULL
                WHEN SUM(nmi_consumption) = 0 THEN NULL
                ELSE (SUM(nmi_consumption) - SUM(building_consumption)) / SUM(nmi_consumption)
            END AS difference_ratio_to_nmi
        FROM gold.gold_daily_nmi_building_reconciliation
        GROUP BY campus_id, usage_month
        """
    )


def _table_result(connection, table_name: str, description: str) -> ReconciliationTable:
    row_count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    return ReconciliationTable(table_name=table_name, row_count=int(row_count), description=description)


def render_reconciliation_summary(tables: list[ReconciliationTable], db_path: Path) -> str:
    """Render a short CLI summary."""

    lines = [f"Wrote reconciliation tables to {db_path}", f"Tables: {len(tables)}"]
    for table in tables:
        lines.append(f"- {table.table_name}: {table.row_count} rows")
    return "\n".join(lines)


def write_reconciliation_report(
    tables: list[ReconciliationTable],
    db_path: Path,
    output_path: Path,
) -> Path:
    """Write a markdown reconciliation report."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# NMI Building Reconciliation Report",
        "",
        "## Purpose",
        "",
        "This report confirms that campus-level NMI usage was compared against summed campus-level building usage.",
        "",
        "## What This Built",
        "",
        "- Daily NMI versus building usage reconciliation",
        "- Monthly NMI versus building usage reconciliation",
        "- Absolute usage difference and ratio to NMI usage",
        "",
        "## Why This Matters",
        "",
        "NMI readings are campus/meter-level in this dataset, not building-level. This check shows how closely campus NMI totals align with summed building meter totals before using them interchangeably.",
        "",
        f"DuckDB database: `{db_path}`",
        "",
        "| Table | Rows | Why |",
        "| --- | ---: | --- |",
    ]
    for table in tables:
        lines.append(f"| `{table.table_name}` | {table.row_count} | {table.description} |")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for reconciliation."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Build NMI versus building reconciliation tables.")
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument("--report-path", type=Path, default=Path("reports/reconciliation_report.md"))
    args = parser.parse_args()

    tables = build_reconciliation_tables(args.db_path)
    print(render_reconciliation_summary(tables, args.db_path))
    report_path = write_reconciliation_report(tables, args.db_path, args.report_path)
    print(f"Wrote reconciliation report to {report_path}")


if __name__ == "__main__":
    main()
