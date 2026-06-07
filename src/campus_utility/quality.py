"""Data-quality checks for silver electricity tables."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb


@dataclass(frozen=True)
class QualityCheck:
    """Result for one quality check."""

    name: str
    table_name: str
    status: str
    observed_value: int | str
    expected: str
    description: str


def run_quality_checks(db_path: Path) -> list[QualityCheck]:
    """Run silver data-quality checks."""

    checks: list[QualityCheck] = []
    with connect_duckdb(db_path) as connection:
        checks.extend(_table_row_count_checks(connection))
        checks.extend(_required_field_checks(connection))
        checks.extend(_non_negative_checks(connection))
        checks.extend(_duplicate_key_checks(connection))
        checks.extend(_timestamp_coverage_checks(connection))
        checks.extend(_campus_reference_checks(connection))
    return checks


def _table_row_count_checks(connection) -> list[QualityCheck]:
    tables = [
        "silver.silver_building_electricity_readings",
        "silver.silver_nmi_electricity_readings",
        "silver.silver_submeter_electricity_readings",
    ]
    checks = []
    for table in tables:
        row_count = _scalar(connection, f"SELECT COUNT(*) FROM {table}")
        checks.append(
            QualityCheck(
                name="row_count_positive",
                table_name=table,
                status=_status(row_count > 0),
                observed_value=row_count,
                expected="> 0",
                description="Silver table should contain rows after transformation.",
            )
        )
    return checks


def _required_field_checks(connection) -> list[QualityCheck]:
    specs = {
        "silver.silver_building_electricity_readings": (
            "campus_id IS NULL OR meter_id IS NULL OR reading_timestamp IS NULL "
            "OR consumption IS NULL OR source_system IS NULL"
        ),
        "silver.silver_nmi_electricity_readings": (
            "campus_id IS NULL OR meter_id IS NULL OR reading_timestamp IS NULL "
            "OR consumption IS NULL OR demand_kw IS NULL OR demand_kva IS NULL OR source_system IS NULL"
        ),
        "silver.silver_submeter_electricity_readings": (
            "campus_id IS NULL OR building_id IS NULL OR meter_id IS NULL "
            "OR reading_timestamp IS NULL OR consumption IS NULL OR current IS NULL "
            "OR voltage IS NULL OR power IS NULL OR power_factor IS NULL OR source_system IS NULL"
        ),
    }
    return [
        _zero_count_check(
            connection,
            name="required_fields_not_null",
            table_name=table,
            predicate=predicate,
            description="Required silver fields should not be null.",
        )
        for table, predicate in specs.items()
    ]


def _non_negative_checks(connection) -> list[QualityCheck]:
    return [
        _zero_count_check(
            connection,
            name="consumption_non_negative",
            table_name=table,
            predicate="consumption < 0",
            description="Consumption should be non-negative in silver.",
        )
        for table in [
            "silver.silver_building_electricity_readings",
            "silver.silver_nmi_electricity_readings",
            "silver.silver_submeter_electricity_readings",
        ]
    ]


def _duplicate_key_checks(connection) -> list[QualityCheck]:
    specs = {
        "silver.silver_building_electricity_readings": "campus_id, meter_id, reading_timestamp",
        "silver.silver_nmi_electricity_readings": "campus_id, meter_id, reading_timestamp",
        "silver.silver_submeter_electricity_readings": (
            "campus_id, building_id, meter_id, reading_timestamp"
        ),
    }
    checks = []
    for table, key_columns in specs.items():
        duplicate_count = _scalar(
            connection,
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT {key_columns}, COUNT(*) AS row_count
                FROM {table}
                GROUP BY {key_columns}
                HAVING COUNT(*) > 1
            )
            """,
        )
        checks.append(
            QualityCheck(
                name="duplicate_key_count",
                table_name=table,
                status=_status(duplicate_count == 0),
                observed_value=duplicate_count,
                expected="0",
                description=f"No duplicate records for key: {key_columns}.",
            )
        )
    return checks


def _timestamp_coverage_checks(connection) -> list[QualityCheck]:
    tables = [
        "silver.silver_building_electricity_readings",
        "silver.silver_nmi_electricity_readings",
        "silver.silver_submeter_electricity_readings",
    ]
    checks = []
    for table in tables:
        minimum, maximum = connection.execute(
            f"SELECT MIN(reading_timestamp), MAX(reading_timestamp) FROM {table}"
        ).fetchone()
        observed = f"{minimum} to {maximum}"
        checks.append(
            QualityCheck(
                name="timestamp_coverage_present",
                table_name=table,
                status=_status(minimum is not None and maximum is not None),
                observed_value=observed,
                expected="non-null min and max",
                description="Timestamp coverage should be present for each silver table.",
            )
        )
    return checks


def _campus_reference_checks(connection) -> list[QualityCheck]:
    checks = []
    for table in [
        "silver.silver_building_electricity_readings",
        "silver.silver_nmi_electricity_readings",
        "silver.silver_submeter_electricity_readings",
    ]:
        missing_count = _scalar(
            connection,
            f"""
            SELECT COUNT(*)
            FROM {table} silver_table
            LEFT JOIN bronze.bronze_campus_meta campus
              ON silver_table.campus_id = campus.id
            WHERE campus.id IS NULL
            """,
        )
        checks.append(
            QualityCheck(
                name="campus_reference_exists",
                table_name=table,
                status=_status(missing_count == 0),
                observed_value=missing_count,
                expected="0",
                description="Silver campus IDs should exist in bronze campus metadata.",
            )
        )
    return checks


def _zero_count_check(
    connection,
    *,
    name: str,
    table_name: str,
    predicate: str,
    description: str,
) -> QualityCheck:
    count = _scalar(connection, f"SELECT COUNT(*) FROM {table_name} WHERE {predicate}")
    return QualityCheck(
        name=name,
        table_name=table_name,
        status=_status(count == 0),
        observed_value=count,
        expected="0",
        description=description,
    )


def _scalar(connection, sql: str) -> int:
    return int(connection.execute(sql).fetchone()[0])


def _status(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def render_quality_summary(checks: list[QualityCheck]) -> str:
    """Render a short CLI summary."""

    passed = sum(check.status == "PASS" for check in checks)
    failed = len(checks) - passed
    return f"Quality checks: {passed} passed, {failed} failed"


def write_quality_report(checks: list[QualityCheck], db_path: Path, output_path: Path) -> Path:
    """Write a markdown data-quality report."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Data Quality Report",
        "",
        "## Purpose",
        "",
        "This report validates cleaned silver electricity tables before they are used for metrics, marts, emissions estimates, or dashboards.",
        "",
        "## What This Checks",
        "",
        "- Silver tables have rows",
        "- Required fields are not null",
        "- Consumption is non-negative",
        "- Meter/timestamp keys are not duplicated",
        "- Timestamp coverage exists",
        "- Campus IDs map to campus metadata",
        "",
        "## Why This Matters",
        "",
        "These checks catch broken cleaning logic and data issues before analytics are built on top of the silver layer.",
        "",
        f"DuckDB database: `{db_path}`",
        "",
        "| Check | Table | Status | Observed | Expected | Why |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for check in checks:
        lines.append(
            f"| `{check.name}` | `{check.table_name}` | {check.status} | "
            f"{check.observed_value} | {check.expected} | {check.description} |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for data-quality checks."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Run data-quality checks on silver tables.")
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument("--report-path", type=Path, default=Path("reports/data_quality_report.md"))
    args = parser.parse_args()

    checks = run_quality_checks(args.db_path)
    print(render_quality_summary(checks))
    report_path = write_quality_report(checks, args.db_path, args.report_path)
    print(f"Wrote quality report to {report_path}")

    if any(check.status == "FAIL" for check in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
