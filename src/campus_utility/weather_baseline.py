"""Weather-normalized electricity usage baseline."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb

BASELINE_MODEL_VERSION = "grouped_median_weather_time_v1"


@dataclass(frozen=True)
class BaselineTable:
    """Metadata for the weather-normalized baseline table."""

    table_name: str
    row_count: int
    high_usage_candidate_count: int


def build_weather_baseline(db_path: Path) -> BaselineTable:
    """Create weather-normalized usage baseline table."""

    with connect_duckdb(db_path) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
        connection.execute("DROP TABLE IF EXISTS gold.gold_weather_normalized_usage")
        connection.execute(
            f"""
            CREATE TABLE gold.gold_weather_normalized_usage AS
            WITH hourly_weather AS (
                SELECT
                    campus_id,
                    DATE_TRUNC('hour', timestamp) AS usage_hour,
                    AVG(air_temperature) AS air_temperature,
                    AVG(apparent_temperature) AS apparent_temperature,
                    AVG(relative_humidity) AS relative_humidity
                FROM bronze.bronze_weather_data
                WHERE air_temperature IS NOT NULL
                GROUP BY campus_id, usage_hour
            ),
            usage_weather AS (
                SELECT
                    usage.campus_id,
                    usage.source_system,
                    usage.meter_id,
                    usage.building_id,
                    usage.usage_hour,
                    CAST(usage.usage_hour AS DATE) AS usage_date,
                    usage.total_consumption AS actual_consumption,
                    weather.air_temperature,
                    weather.apparent_temperature,
                    weather.relative_humidity,
                    EXTRACT(hour FROM usage.usage_hour)::INTEGER AS hour_of_day,
                    EXTRACT(dow FROM usage.usage_hour)::INTEGER AS day_of_week,
                    EXTRACT(month FROM usage.usage_hour)::INTEGER AS usage_month_number,
                    FLOOR(weather.air_temperature / 5) * 5 AS temperature_band_c
                FROM gold.gold_hourly_electricity_usage usage
                JOIN hourly_weather weather
                  ON usage.campus_id = weather.campus_id
                 AND usage.usage_hour = weather.usage_hour
                WHERE usage.total_consumption >= 0
            ),
            baseline AS (
                SELECT
                    campus_id,
                    source_system,
                    meter_id,
                    building_id,
                    hour_of_day,
                    day_of_week,
                    usage_month_number,
                    temperature_band_c,
                    MEDIAN(actual_consumption) AS expected_consumption
                FROM usage_weather
                GROUP BY
                    campus_id,
                    source_system,
                    meter_id,
                    building_id,
                    hour_of_day,
                    day_of_week,
                    usage_month_number,
                    temperature_band_c
            ),
            scored AS (
                SELECT
                    usage_weather.*,
                    baseline.expected_consumption,
                    usage_weather.actual_consumption - baseline.expected_consumption
                        AS residual_consumption,
                    CASE
                        WHEN baseline.expected_consumption = 0 THEN NULL
                        ELSE (
                            usage_weather.actual_consumption - baseline.expected_consumption
                        ) / baseline.expected_consumption
                    END AS residual_percent
                FROM usage_weather
                JOIN baseline
                  ON usage_weather.campus_id = baseline.campus_id
                 AND usage_weather.source_system = baseline.source_system
                 AND usage_weather.meter_id = baseline.meter_id
                 AND COALESCE(usage_weather.building_id, -1) = COALESCE(baseline.building_id, -1)
                 AND usage_weather.hour_of_day = baseline.hour_of_day
                 AND usage_weather.day_of_week = baseline.day_of_week
                 AND usage_weather.usage_month_number = baseline.usage_month_number
                 AND usage_weather.temperature_band_c = baseline.temperature_band_c
            )
            SELECT
                campus_id,
                source_system,
                meter_id,
                building_id,
                usage_hour,
                usage_date,
                actual_consumption,
                expected_consumption,
                residual_consumption,
                residual_percent,
                air_temperature,
                apparent_temperature,
                relative_humidity,
                hour_of_day,
                day_of_week,
                usage_month_number,
                temperature_band_c,
                '{BASELINE_MODEL_VERSION}' AS baseline_model_version,
                CASE
                    WHEN residual_percent >= 0.25 AND residual_consumption > 0 THEN TRUE
                    ELSE FALSE
                END AS is_high_usage_candidate,
                CASE
                    WHEN residual_percent IS NULL OR residual_consumption <= 0 THEN 0
                    ELSE LEAST(100, ROUND(residual_percent * 100, 2))
                END AS efficiency_opportunity_score
            FROM scored
            """
        )
        row_count, high_usage_count = connection.execute(
            """
            SELECT
                COUNT(*),
                COUNT(*) FILTER (WHERE is_high_usage_candidate)
            FROM gold.gold_weather_normalized_usage
            """
        ).fetchone()

    return BaselineTable(
        table_name="gold.gold_weather_normalized_usage",
        row_count=int(row_count),
        high_usage_candidate_count=int(high_usage_count),
    )


def render_baseline_summary(table: BaselineTable, db_path: Path) -> str:
    """Render a short CLI summary."""

    return (
        f"Wrote weather baseline to {db_path}\n"
        f"- {table.table_name}: {table.row_count} rows\n"
        f"- high-usage candidates: {table.high_usage_candidate_count}"
    )


def write_baseline_report(table: BaselineTable, db_path: Path, output_path: Path) -> Path:
    """Write a markdown report for the weather-normalized baseline."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Weather-Normalized Baseline Report",
        "",
        "## Purpose",
        "",
        "This report confirms that electricity usage was compared with an explainable weather and time baseline.",
        "",
        "## What This Built",
        "",
        "- `gold.gold_weather_normalized_usage`",
        "- Actual consumption",
        "- Expected consumption from grouped medians",
        "- Residual consumption and residual percent",
        "- High-usage candidate flag and opportunity score",
        "",
        "## Why This Matters",
        "",
        "This moves the project from usage reporting to decision-support analytics by identifying usage that is high relative to similar weather and time conditions.",
        "",
        "## Model",
        "",
        f"`{BASELINE_MODEL_VERSION}` uses median usage grouped by campus, source, meter, optional building, hour of day, day of week, month, and 5-degree Celsius temperature band.",
        "",
        "## Limitation",
        "",
        "High-usage candidates are not confirmed waste, faults, or savings. They are records worth investigation.",
        "",
        f"DuckDB database: `{db_path}`",
        "",
        "| Table | Rows | High-Usage Candidates |",
        "| --- | ---: | ---: |",
        f"| `{table.table_name}` | {table.row_count} | {table.high_usage_candidate_count} |",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for weather-normalized baseline."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Build weather-normalized usage baseline.")
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument("--report-path", type=Path, default=Path("reports/weather_baseline_report.md"))
    args = parser.parse_args()

    table = build_weather_baseline(args.db_path)
    print(render_baseline_summary(table, args.db_path))
    report_path = write_baseline_report(table, args.db_path, args.report_path)
    print(f"Wrote baseline report to {report_path}")


if __name__ == "__main__":
    main()
