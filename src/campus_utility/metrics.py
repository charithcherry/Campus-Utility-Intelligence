"""Gold usage and peak-demand metrics."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb


@dataclass(frozen=True)
class MetricTable:
    """Metadata for one gold metric table."""

    table_name: str
    row_count: int
    description: str


GOLD_TABLES = (
    "gold.gold_hourly_electricity_usage",
    "gold.gold_daily_electricity_usage",
    "gold.gold_monthly_electricity_usage",
    "gold.gold_peak_demand",
)


def build_gold_metrics(db_path: Path) -> list[MetricTable]:
    """Build gold electricity usage and peak-demand metric tables."""

    with connect_duckdb(db_path) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
        _create_hourly_usage(connection)
        _create_daily_usage(connection)
        _create_monthly_usage(connection)
        _create_peak_demand(connection)

        return [
            _metric_result(
                connection,
                "gold.gold_hourly_electricity_usage",
                "Hourly electricity consumption by campus, source, and meter.",
            ),
            _metric_result(
                connection,
                "gold.gold_daily_electricity_usage",
                "Daily electricity consumption by campus and source.",
            ),
            _metric_result(
                connection,
                "gold.gold_monthly_electricity_usage",
                "Monthly electricity consumption by campus and source.",
            ),
            _metric_result(
                connection,
                "gold.gold_peak_demand",
                "Observed peak demand from NMI readings by campus and meter.",
            ),
        ]


def _create_hourly_usage(connection) -> None:
    connection.execute("DROP TABLE IF EXISTS gold.gold_hourly_electricity_usage")
    connection.execute(
        """
        CREATE TABLE gold.gold_hourly_electricity_usage AS
        WITH electricity_readings AS (
            SELECT
                campus_id,
                meter_id,
                NULL::BIGINT AS building_id,
                reading_timestamp,
                consumption,
                source_system
            FROM silver.silver_building_electricity_readings

            UNION ALL

            SELECT
                campus_id,
                meter_id,
                NULL::BIGINT AS building_id,
                reading_timestamp,
                consumption,
                source_system
            FROM silver.silver_nmi_electricity_readings

            UNION ALL

            SELECT
                campus_id,
                meter_id,
                building_id,
                reading_timestamp,
                consumption,
                source_system
            FROM silver.silver_submeter_electricity_readings
        )
        SELECT
            campus_id,
            source_system,
            meter_id,
            building_id,
            DATE_TRUNC('hour', reading_timestamp) AS usage_hour,
            SUM(consumption) AS total_consumption,
            COUNT(*) AS reading_count,
            MIN(reading_timestamp) AS first_reading_timestamp,
            MAX(reading_timestamp) AS last_reading_timestamp
        FROM electricity_readings
        GROUP BY campus_id, source_system, meter_id, building_id, usage_hour
        """
    )


def _create_daily_usage(connection) -> None:
    connection.execute("DROP TABLE IF EXISTS gold.gold_daily_electricity_usage")
    connection.execute(
        """
        CREATE TABLE gold.gold_daily_electricity_usage AS
        SELECT
            campus_id,
            source_system,
            CAST(usage_hour AS DATE) AS usage_date,
            SUM(total_consumption) AS total_consumption,
            SUM(reading_count) AS reading_count,
            COUNT(DISTINCT meter_id) AS meter_count
        FROM gold.gold_hourly_electricity_usage
        GROUP BY campus_id, source_system, usage_date
        """
    )


def _create_monthly_usage(connection) -> None:
    connection.execute("DROP TABLE IF EXISTS gold.gold_monthly_electricity_usage")
    connection.execute(
        """
        CREATE TABLE gold.gold_monthly_electricity_usage AS
        SELECT
            campus_id,
            source_system,
            DATE_TRUNC('month', usage_date)::DATE AS usage_month,
            SUM(total_consumption) AS total_consumption,
            SUM(reading_count) AS reading_count,
            MAX(meter_count) AS max_daily_meter_count
        FROM gold.gold_daily_electricity_usage
        GROUP BY campus_id, source_system, usage_month
        """
    )


def _create_peak_demand(connection) -> None:
    connection.execute("DROP TABLE IF EXISTS gold.gold_peak_demand")
    connection.execute(
        """
        CREATE TABLE gold.gold_peak_demand AS
        SELECT
            campus_id,
            meter_id,
            reading_timestamp AS peak_timestamp,
            demand_kw AS peak_demand_kw,
            demand_kva AS peak_demand_kva,
            consumption AS consumption_at_peak
        FROM silver.silver_nmi_electricity_readings
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY campus_id, meter_id
            ORDER BY demand_kw DESC, reading_timestamp
        ) = 1
        """
    )


def _metric_result(connection, table_name: str, description: str) -> MetricTable:
    row_count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    return MetricTable(table_name=table_name, row_count=int(row_count), description=description)


def render_metrics_summary(tables: list[MetricTable], db_path: Path) -> str:
    """Render a short CLI summary for gold metrics."""

    lines = [f"Wrote gold metrics to {db_path}", f"Metric tables: {len(tables)}"]
    for table in tables:
        lines.append(f"- {table.table_name}: {table.row_count} rows")
    return "\n".join(lines)


def write_metrics_report(tables: list[MetricTable], db_path: Path, output_path: Path) -> Path:
    """Write a markdown report for gold metric tables."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Gold Metrics Report",
        "",
        "## Purpose",
        "",
        "This report confirms that cleaned silver electricity readings were aggregated into gold usage and peak-demand tables.",
        "",
        "## What This Built",
        "",
        "- Hourly electricity usage by campus, source, meter, and building where available",
        "- Daily electricity usage by campus and source",
        "- Monthly electricity usage by campus and source",
        "- Peak NMI demand by campus and meter",
        "",
        "## Why This Matters",
        "",
        "Gold tables are reporting-ready outputs for SQL analysis, facility energy trends, peak-demand review, and dashboards.",
        "",
        f"DuckDB database: `{db_path}`",
        "",
        "| Gold Table | Rows | Why |",
        "| --- | ---: | --- |",
    ]
    for table in tables:
        lines.append(f"| `{table.table_name}` | {table.row_count} | {table.description} |")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for gold metrics."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Build gold electricity metric tables.")
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument("--report-path", type=Path, default=Path("reports/gold_metrics_report.md"))
    args = parser.parse_args()

    tables = build_gold_metrics(args.db_path)
    print(render_metrics_summary(tables, args.db_path))
    report_path = write_metrics_report(tables, args.db_path, args.report_path)
    print(f"Wrote metrics report to {report_path}")


if __name__ == "__main__":
    main()
