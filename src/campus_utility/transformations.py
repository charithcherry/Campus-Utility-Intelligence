"""Silver transformations for campus utility electricity data."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb


@dataclass(frozen=True)
class TransformedTable:
    """Metadata for one transformed silver table."""

    table_name: str
    row_count: int
    source_table: str


SILVER_TABLES = (
    "silver.silver_building_electricity_readings",
    "silver.silver_nmi_electricity_readings",
    "silver.silver_submeter_electricity_readings",
)


def transform_silver_tables(db_path: Path) -> list[TransformedTable]:
    """Create cleaned silver electricity tables from bronze tables."""

    with connect_duckdb(db_path) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS silver")
        _create_building_electricity(connection)
        _create_nmi_electricity(connection)
        _create_submeter_electricity(connection)

        return [
            _table_result(
                connection,
                "silver.silver_building_electricity_readings",
                "bronze.bronze_building_consumption",
            ),
            _table_result(
                connection,
                "silver.silver_nmi_electricity_readings",
                "bronze.bronze_nmi_consumption",
            ),
            _table_result(
                connection,
                "silver.silver_submeter_electricity_readings",
                "bronze.bronze_building_submeter_consumption",
            ),
        ]


def _create_building_electricity(connection) -> None:
    connection.execute("DROP TABLE IF EXISTS silver.silver_building_electricity_readings")
    connection.execute(
        """
        CREATE TABLE silver.silver_building_electricity_readings AS
        SELECT
            CAST(campus_id AS BIGINT) AS campus_id,
            CAST(meter_id AS BIGINT) AS meter_id,
            CAST(timestamp AS TIMESTAMP) AS reading_timestamp,
            CAST(consumption AS DOUBLE) AS consumption,
            'building_consumption' AS source_system
        FROM bronze.bronze_building_consumption
        WHERE campus_id IS NOT NULL
          AND meter_id IS NOT NULL
          AND timestamp IS NOT NULL
          AND consumption IS NOT NULL
          AND consumption >= 0
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY campus_id, meter_id, timestamp
            ORDER BY consumption
        ) = 1
        """
    )


def _create_nmi_electricity(connection) -> None:
    connection.execute("DROP TABLE IF EXISTS silver.silver_nmi_electricity_readings")
    connection.execute(
        """
        CREATE TABLE silver.silver_nmi_electricity_readings AS
        SELECT
            TRY_CAST(campus_id AS BIGINT) AS campus_id,
            CAST(meter_id AS BIGINT) AS meter_id,
            CAST(timestamp AS TIMESTAMP) AS reading_timestamp,
            CAST(consumption AS DOUBLE) AS consumption,
            CAST(demand_kW AS DOUBLE) AS demand_kw,
            CAST(demand_kVA AS DOUBLE) AS demand_kva,
            'nmi_consumption' AS source_system
        FROM bronze.bronze_nmi_consumption
        WHERE TRY_CAST(campus_id AS BIGINT) IS NOT NULL
          AND meter_id IS NOT NULL
          AND timestamp IS NOT NULL
          AND consumption IS NOT NULL
          AND consumption >= 0
          AND demand_kW IS NOT NULL
          AND demand_kVA IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY TRY_CAST(campus_id AS BIGINT), meter_id, timestamp
            ORDER BY consumption, demand_kW, demand_kVA
        ) = 1
        """
    )


def _create_submeter_electricity(connection) -> None:
    connection.execute("DROP TABLE IF EXISTS silver.silver_submeter_electricity_readings")
    connection.execute(
        """
        CREATE TABLE silver.silver_submeter_electricity_readings AS
        SELECT
            CAST(campus_id AS BIGINT) AS campus_id,
            CAST(building_id AS BIGINT) AS building_id,
            CAST(id AS BIGINT) AS meter_id,
            CAST(timestamp AS TIMESTAMP) AS reading_timestamp,
            CAST(consumption AS DOUBLE) AS consumption,
            CAST(current AS DOUBLE) AS current,
            CAST(voltage AS DOUBLE) AS voltage,
            CAST(power AS DOUBLE) AS power,
            CAST(power_factor AS DOUBLE) AS power_factor,
            'building_submeter_consumption' AS source_system
        FROM bronze.bronze_building_submeter_consumption
        WHERE campus_id IS NOT NULL
          AND building_id IS NOT NULL
          AND id IS NOT NULL
          AND timestamp IS NOT NULL
          AND consumption IS NOT NULL
          AND consumption >= 0
          AND current IS NOT NULL
          AND voltage IS NOT NULL
          AND power IS NOT NULL
          AND power_factor IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY campus_id, building_id, id, timestamp
            ORDER BY consumption, power
        ) = 1
        """
    )


def _table_result(connection, table_name: str, source_table: str) -> TransformedTable:
    row_count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    return TransformedTable(table_name=table_name, row_count=int(row_count), source_table=source_table)


def render_transform_summary(tables: list[TransformedTable], db_path: Path) -> str:
    """Render a CLI summary for silver transformations."""

    lines = [f"Wrote silver tables to {db_path}", f"Transformed tables: {len(tables)}"]
    for table in tables:
        lines.append(f"- {table.table_name}: {table.row_count} rows from {table.source_table}")
    return "\n".join(lines)


def write_transform_report(tables: list[TransformedTable], db_path: Path, output_path: Path) -> Path:
    """Write a markdown report for silver transformation results."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Silver Transformation Report",
        "",
        "## Purpose",
        "",
        "This report confirms that bronze electricity readings were cleaned into silver tables for downstream analytics.",
        "",
        "## What This Cleaned",
        "",
        "- Removed rows missing required IDs, timestamps, or consumption values",
        "- Removed rows with negative consumption",
        "- Deduplicated repeated meter/timestamp records",
        "- Standardized timestamp and numeric reading columns",
        "- Kept building, NMI, and submeter readings separate because they have different grains",
        "",
        "## Why This Matters",
        "",
        "Silver tables are cleaner inputs for data-quality checks, gold marts, peak-demand metrics, emissions estimates, and dashboards. Bronze stays raw for auditability.",
        "",
        f"DuckDB database: `{db_path}`",
        "",
        "| Source Table | Silver Table | Rows |",
        "| --- | --- | ---: |",
    ]
    for table in tables:
        lines.append(f"| `{table.source_table}` | `{table.table_name}` | {table.row_count} |")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for silver transformations."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Create silver electricity tables in DuckDB.")
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument("--report-path", type=Path, default=Path("reports/silver_transform_report.md"))
    args = parser.parse_args()

    tables = transform_silver_tables(args.db_path)
    print(render_transform_summary(tables, args.db_path))
    report_path = write_transform_report(tables, args.db_path, args.report_path)
    print(f"Wrote transform report to {report_path}")


if __name__ == "__main__":
    main()
