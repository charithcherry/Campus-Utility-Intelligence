"""Estimated electricity emissions metrics."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb

REQUIRED_FACTOR_COLUMNS = {
    "factor_id",
    "country",
    "region",
    "source_system",
    "energy_type",
    "factor_year",
    "emissions_factor_kg_co2e_per_kwh",
    "factor_source_name",
    "factor_source_url",
    "is_default",
    "notes",
}


@dataclass(frozen=True)
class EmissionsTable:
    """Metadata for the emissions metric table."""

    table_name: str
    row_count: int
    factor_count: int
    default_factor_count: int


def load_emissions_factors(factors_path: Path) -> pd.DataFrame:
    """Load emissions factor reference data from CSV."""

    if not factors_path.exists():
        raise FileNotFoundError(f"Emissions factor file not found: {factors_path}")

    factors = pd.read_csv(factors_path, keep_default_na=False)
    missing_columns = REQUIRED_FACTOR_COLUMNS - set(factors.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Emissions factor file missing required columns: {missing}")

    factors["factor_year"] = factors["factor_year"].astype(int)
    factors["emissions_factor_kg_co2e_per_kwh"] = factors[
        "emissions_factor_kg_co2e_per_kwh"
    ].astype(float)
    factors["is_default"] = factors["is_default"].astype(str).str.lower().isin(["true", "1", "yes"])
    return factors


def build_emissions_metrics(db_path: Path, factors_path: Path) -> EmissionsTable:
    """Build estimated monthly electricity emissions from gold monthly usage."""

    factors = load_emissions_factors(factors_path)

    with connect_duckdb(db_path) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS reference")
        connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
        connection.execute("DROP TABLE IF EXISTS reference.reference_emissions_factors")
        connection.register("emissions_factors_df", factors)
        connection.execute(
            """
            CREATE TABLE reference.reference_emissions_factors AS
            SELECT * FROM emissions_factors_df
            """
        )
        connection.unregister("emissions_factors_df")

        connection.execute("DROP TABLE IF EXISTS gold.gold_electricity_emissions")
        connection.execute(
            """
            CREATE TABLE gold.gold_electricity_emissions AS
            WITH usage AS (
                SELECT
                    campus_id,
                    source_system,
                    usage_month,
                    EXTRACT(year FROM usage_month)::INTEGER AS usage_year,
                    total_consumption
                FROM gold.gold_monthly_electricity_usage
            ),
            matched AS (
                SELECT
                    usage.*,
                    factor.factor_id,
                    factor.country,
                    factor.region,
                    factor.energy_type,
                    factor.factor_year,
                    factor.emissions_factor_kg_co2e_per_kwh,
                    factor.factor_source_name,
                    factor.factor_source_url,
                    factor.is_default,
                    factor.notes,
                    ROW_NUMBER() OVER (
                        PARTITION BY usage.campus_id, usage.source_system, usage.usage_month
                        ORDER BY
                            CASE WHEN factor.source_system = usage.source_system THEN 0 ELSE 1 END,
                            CASE WHEN factor.factor_year = usage.usage_year THEN 0 ELSE 1 END,
                            factor.is_default,
                            factor.factor_year DESC
                    ) AS factor_rank
                FROM usage
                JOIN reference.reference_emissions_factors factor
                 ON factor.energy_type = 'electricity'
                 AND factor.country = 'Australia'
                 AND (factor.factor_year <= usage.usage_year OR factor.is_default)
                 AND (factor.source_system = usage.source_system OR factor.source_system = '*')
            )
            SELECT
                campus_id,
                source_system,
                usage_month,
                total_consumption,
                factor_id,
                country AS factor_country,
                region AS factor_region,
                energy_type,
                factor_year,
                emissions_factor_kg_co2e_per_kwh,
                factor_source_name,
                factor_source_url,
                is_default AS used_default_factor,
                notes AS factor_notes,
                total_consumption * emissions_factor_kg_co2e_per_kwh
                    AS estimated_emissions_kg_co2e
            FROM matched
            WHERE factor_rank = 1
            """
        )
        row_count = connection.execute(
            "SELECT COUNT(*) FROM gold.gold_electricity_emissions"
        ).fetchone()[0]
        factor_count = connection.execute(
            "SELECT COUNT(*) FROM reference.reference_emissions_factors"
        ).fetchone()[0]
        default_factor_count = connection.execute(
            "SELECT COUNT(*) FROM gold.gold_electricity_emissions WHERE used_default_factor"
        ).fetchone()[0]

    return EmissionsTable(
        table_name="gold.gold_electricity_emissions",
        row_count=int(row_count),
        factor_count=int(factor_count),
        default_factor_count=int(default_factor_count),
    )


def render_emissions_summary(table: EmissionsTable, db_path: Path) -> str:
    """Render a short CLI summary."""

    return (
        f"Wrote emissions metrics to {db_path}\n"
        f"- {table.table_name}: {table.row_count} rows\n"
        f"- reference.reference_emissions_factors: {table.factor_count} factors\n"
        f"- rows using default factors: {table.default_factor_count}"
    )


def write_emissions_report(table: EmissionsTable, db_path: Path, output_path: Path) -> Path:
    """Write a markdown report for estimated emissions."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Emissions Metrics Report",
        "",
        "## Purpose",
        "",
        "This report confirms that monthly electricity usage was converted into estimated emissions using configurable emissions factor reference data.",
        "",
        "## What This Built",
        "",
        "- `reference.reference_emissions_factors`",
        "- `gold.gold_electricity_emissions`",
        "- Estimated emissions by campus, source, and month",
        "- Factor value, source metadata, default flag, and notes on every emissions row",
        "",
        "## Why This Matters",
        "",
        "Factor metadata makes the emissions estimate auditable and replaceable when official region/year factors are available.",
        "",
        "## Assumption",
        "",
        "Emissions are estimates, not official carbon accounting results. Default factors are demo estimates unless replaced by user-provided reference data.",
        "",
        f"DuckDB database: `{db_path}`",
        "",
        "| Table | Rows |",
        "| --- | ---: |",
        f"| `{table.table_name}` | {table.row_count} |",
        f"| `reference.reference_emissions_factors` | {table.factor_count} |",
        "",
        f"Rows using default factors: `{table.default_factor_count}`",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for emissions metrics."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Build estimated electricity emissions metrics.")
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument("--factors-path", type=Path, default=config.emissions_factors_path)
    parser.add_argument("--report-path", type=Path, default=Path("reports/emissions_metrics_report.md"))
    args = parser.parse_args()

    table = build_emissions_metrics(args.db_path, args.factors_path)
    print(render_emissions_summary(table, args.db_path))
    report_path = write_emissions_report(table, args.db_path, args.report_path)
    print(f"Wrote emissions report to {report_path}")


if __name__ == "__main__":
    main()
