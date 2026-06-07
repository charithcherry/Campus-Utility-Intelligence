"""Time-varying grid carbon-intensity workflow."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb

REQUIRED_GRID_INTENSITY_COLUMNS = {
    "region_code",
    "region_name",
    "interval_start",
    "interval_end",
    "emissions_intensity_kg_co2e_per_kwh",
    "source_name",
    "source_url",
    "data_version",
    "notes",
}

REFERENCE_TABLE = "reference.reference_grid_carbon_intensity_hourly"
GOLD_TABLE = "gold.gold_hourly_time_varying_emissions"
DEFAULT_REGION_CODE = "VIC1"


@dataclass(frozen=True)
class CarbonIntensityTable:
    """Metadata for time-varying emissions outputs."""

    reference_table_name: str
    reference_row_count: int
    gold_table_name: str
    gold_row_count: int
    matched_hourly_factor_count: int
    fallback_static_factor_count: int
    missing_hourly_factor_count: int
    input_path: Path
    input_file_found: bool


def load_grid_carbon_intensity(intensity_path: Path) -> pd.DataFrame:
    """Load and validate grid carbon-intensity reference data."""

    if not intensity_path.exists():
        return _empty_intensity_frame()

    intensity = pd.read_csv(intensity_path, keep_default_na=False)
    if intensity.empty:
        raise ValueError(f"Grid carbon-intensity file is empty: {intensity_path}")

    missing_columns = REQUIRED_GRID_INTENSITY_COLUMNS - set(intensity.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Grid carbon-intensity file missing required columns: {missing}")

    intensity = intensity.copy()
    intensity["interval_start"] = _parse_timestamp_column(intensity["interval_start"], "interval_start")
    intensity["interval_end"] = _parse_timestamp_column(intensity["interval_end"], "interval_end")
    intensity["interval_start_hour"] = intensity["interval_start"].dt.floor("h")
    intensity["emissions_intensity_kg_co2e_per_kwh"] = pd.to_numeric(
        intensity["emissions_intensity_kg_co2e_per_kwh"],
        errors="coerce",
    )
    intensity["is_synthetic"] = (
        intensity["notes"].astype(str).str.lower().str.contains("synthetic")
        | intensity["source_name"].astype(str).str.lower().str.contains("synthetic")
    )

    if intensity["interval_start"].isna().any():
        raise ValueError("Grid carbon-intensity file contains null or unparseable interval_start values")
    if intensity["interval_end"].isna().any():
        raise ValueError("Grid carbon-intensity file contains null or unparseable interval_end values")
    if intensity["emissions_intensity_kg_co2e_per_kwh"].isna().any():
        raise ValueError("Grid carbon-intensity file contains null or non-numeric intensity values")
    if (intensity["emissions_intensity_kg_co2e_per_kwh"] < 0).any():
        raise ValueError("Grid carbon-intensity file contains negative emissions intensity values")
    if intensity.duplicated(["region_code", "interval_start_hour"]).any():
        raise ValueError("Grid carbon-intensity file contains duplicate region/hour rows")

    return intensity[
        [
            "region_code",
            "region_name",
            "interval_start",
            "interval_end",
            "interval_start_hour",
            "emissions_intensity_kg_co2e_per_kwh",
            "source_name",
            "source_url",
            "data_version",
            "is_synthetic",
            "notes",
        ]
    ]


def build_time_varying_emissions(
    db_path: Path,
    intensity_path: Path,
    region_code: str = DEFAULT_REGION_CODE,
) -> CarbonIntensityTable:
    """Build hourly time-varying emissions estimates with static fallback."""

    intensity = load_grid_carbon_intensity(intensity_path)
    input_file_found = intensity_path.exists()

    with connect_duckdb(db_path) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS reference")
        connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
        connection.execute(f"DROP TABLE IF EXISTS {REFERENCE_TABLE}")

        if intensity.empty:
            _create_empty_reference_table(connection)
        else:
            connection.register("grid_carbon_intensity_df", intensity)
            connection.execute(
                f"""
                CREATE TABLE {REFERENCE_TABLE} AS
                SELECT
                    region_code,
                    region_name,
                    interval_start,
                    interval_end,
                    interval_start_hour,
                    emissions_intensity_kg_co2e_per_kwh,
                    source_name,
                    source_url,
                    data_version,
                    is_synthetic,
                    CURRENT_TIMESTAMP AS ingested_at,
                    notes
                FROM grid_carbon_intensity_df
                """
            )
            connection.unregister("grid_carbon_intensity_df")

        connection.execute(f"DROP TABLE IF EXISTS {GOLD_TABLE}")
        connection.execute(
            f"""
            CREATE TABLE {GOLD_TABLE} AS
            WITH hourly_usage AS (
                SELECT
                    usage_hour,
                    campus_id,
                    source_system,
                    meter_id,
                    building_id,
                    total_consumption,
                    DATE_TRUNC('month', usage_hour)::DATE AS usage_month
                FROM gold.gold_hourly_electricity_usage
            ),
            static_factors AS (
                SELECT
                    campus_id,
                    source_system,
                    usage_month,
                    emissions_factor_kg_co2e_per_kwh AS static_emissions_factor_kg_co2e_per_kwh,
                    factor_source_name AS static_factor_source_name,
                    factor_source_url AS static_factor_source_url
                FROM gold.gold_electricity_emissions
            ),
            joined AS (
                SELECT
                    usage.usage_hour,
                    usage.campus_id,
                    usage.source_system,
                    usage.meter_id,
                    usage.building_id,
                    usage.total_consumption,
                    static.static_emissions_factor_kg_co2e_per_kwh,
                    usage.total_consumption * static.static_emissions_factor_kg_co2e_per_kwh
                        AS static_estimated_emissions_kg_co2e,
                    intensity.emissions_intensity_kg_co2e_per_kwh
                        AS time_varying_emissions_factor_kg_co2e_per_kwh,
                    usage.total_consumption * intensity.emissions_intensity_kg_co2e_per_kwh
                        AS time_varying_estimated_emissions_kg_co2e,
                    COALESCE(intensity.source_name, static.static_factor_source_name)
                        AS factor_source_name,
                    COALESCE(intensity.source_url, static.static_factor_source_url)
                        AS factor_source_url,
                    CASE
                        WHEN intensity.emissions_intensity_kg_co2e_per_kwh IS NOT NULL
                            THEN 'matched_hourly_factor'
                        WHEN static.static_emissions_factor_kg_co2e_per_kwh IS NOT NULL
                            THEN 'fallback_static_factor'
                        ELSE 'missing_hourly_factor'
                    END AS factor_match_status
                FROM hourly_usage usage
                LEFT JOIN static_factors static
                 ON usage.campus_id = static.campus_id
                 AND usage.source_system = static.source_system
                 AND usage.usage_month = static.usage_month
                LEFT JOIN {REFERENCE_TABLE} intensity
                 ON intensity.region_code = ?
                 AND usage.usage_hour = intensity.interval_start_hour
            )
            SELECT
                usage_hour,
                campus_id,
                source_system,
                meter_id,
                building_id,
                total_consumption,
                static_emissions_factor_kg_co2e_per_kwh,
                static_estimated_emissions_kg_co2e,
                time_varying_emissions_factor_kg_co2e_per_kwh,
                time_varying_estimated_emissions_kg_co2e,
                factor_source_name,
                factor_source_url,
                factor_match_status
            FROM joined
            """,
            [region_code],
        )

        stats = connection.execute(
            f"""
            SELECT
                (SELECT COUNT(*) FROM {REFERENCE_TABLE}) AS reference_row_count,
                COUNT(*) AS gold_row_count,
                COUNT(*) FILTER (WHERE factor_match_status = 'matched_hourly_factor')
                    AS matched_hourly_factor_count,
                COUNT(*) FILTER (WHERE factor_match_status = 'fallback_static_factor')
                    AS fallback_static_factor_count,
                COUNT(*) FILTER (WHERE factor_match_status = 'missing_hourly_factor')
                    AS missing_hourly_factor_count
            FROM {GOLD_TABLE}
            """
        ).fetchone()

    return CarbonIntensityTable(
        reference_table_name=REFERENCE_TABLE,
        reference_row_count=int(stats[0]),
        gold_table_name=GOLD_TABLE,
        gold_row_count=int(stats[1]),
        matched_hourly_factor_count=int(stats[2]),
        fallback_static_factor_count=int(stats[3]),
        missing_hourly_factor_count=int(stats[4]),
        input_path=intensity_path,
        input_file_found=input_file_found,
    )


def render_carbon_intensity_summary(table: CarbonIntensityTable, db_path: Path) -> str:
    """Render a short CLI summary."""

    return (
        f"Wrote time-varying emissions outputs to {db_path}\n"
        f"- {table.reference_table_name}: {table.reference_row_count} rows\n"
        f"- {table.gold_table_name}: {table.gold_row_count} rows\n"
        f"- matched hourly factors: {table.matched_hourly_factor_count}\n"
        f"- fallback static factors: {table.fallback_static_factor_count}\n"
        f"- missing factors: {table.missing_hourly_factor_count}"
    )


def write_carbon_intensity_report(
    table: CarbonIntensityTable,
    db_path: Path,
    output_path: Path,
) -> Path:
    """Write a markdown report for time-varying emissions outputs."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    source_status = "found" if table.input_file_found else "not found"
    lines = [
        "# Time-Varying Carbon Intensity Report",
        "",
        "## Purpose",
        "",
        "This report confirms that optional hourly grid carbon-intensity data was joined to hourly electricity usage when available.",
        "",
        "## What This Built",
        "",
        f"- `{table.reference_table_name}`",
        f"- `{table.gold_table_name}`",
        "- Static DCCEEW emissions remain available for comparison",
        "- Missing hourly factors fall back to the static factor when monthly static emissions exist",
        "",
        "## Why This Matters",
        "",
        "Static DCCEEW Scope 2 estimates and time-varying grid-intensity estimates answer different questions. Static factors support consistent annual/location-based estimates. Time-varying intensity can support operational what-if analysis when valid hourly data exists.",
        "",
        "## Accuracy Notes",
        "",
        "- No official hourly carbon-intensity values are invented.",
        "- Time-varying emissions are optional and source-dependent.",
        "- This is not carbon accounting compliance reporting.",
        "- This is not real-time grid optimization.",
        "",
        f"Input file: `{table.input_path}` ({source_status})",
        f"DuckDB database: `{db_path}`",
        "",
        "| Output | Rows |",
        "| --- | ---: |",
        f"| `{table.reference_table_name}` | {table.reference_row_count} |",
        f"| `{table.gold_table_name}` | {table.gold_row_count} |",
        "",
        "| Match Status | Rows |",
        "| --- | ---: |",
        f"| `matched_hourly_factor` | {table.matched_hourly_factor_count} |",
        f"| `fallback_static_factor` | {table.fallback_static_factor_count} |",
        f"| `missing_hourly_factor` | {table.missing_hourly_factor_count} |",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _parse_timestamp_column(series: pd.Series, column_name: str) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    if parsed.isna().any():
        raise ValueError(f"Grid carbon-intensity file contains unparseable {column_name} values")
    return parsed.dt.tz_convert(None)


def _empty_intensity_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "region_code",
            "region_name",
            "interval_start",
            "interval_end",
            "interval_start_hour",
            "emissions_intensity_kg_co2e_per_kwh",
            "source_name",
            "source_url",
            "data_version",
            "is_synthetic",
            "notes",
        ]
    )


def _create_empty_reference_table(connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE {REFERENCE_TABLE} (
            region_code VARCHAR,
            region_name VARCHAR,
            interval_start TIMESTAMP,
            interval_end TIMESTAMP,
            interval_start_hour TIMESTAMP,
            emissions_intensity_kg_co2e_per_kwh DOUBLE,
            source_name VARCHAR,
            source_url VARCHAR,
            data_version VARCHAR,
            is_synthetic BOOLEAN,
            ingested_at TIMESTAMP WITH TIME ZONE,
            notes VARCHAR
        )
        """
    )


def main() -> None:
    """CLI entry point for time-varying carbon-intensity estimates."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Build optional time-varying emissions estimates.")
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument("--intensity-path", type=Path, default=config.grid_carbon_intensity_path)
    parser.add_argument("--region-code", default=DEFAULT_REGION_CODE)
    parser.add_argument("--report-path", type=Path, default=Path("reports/time_varying_emissions_report.md"))
    args = parser.parse_args()

    table = build_time_varying_emissions(args.db_path, args.intensity_path, args.region_code)
    print(render_carbon_intensity_summary(table, args.db_path))
    report_path = write_carbon_intensity_report(table, args.db_path, args.report_path)
    print(f"Wrote time-varying emissions report to {report_path}")


if __name__ == "__main__":
    main()
