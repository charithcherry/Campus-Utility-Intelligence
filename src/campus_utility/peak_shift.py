"""Offline peak-shifting simulation workflow."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb

DEFAULT_FLEXIBLE_LOAD_PERCENTS = (0.05, 0.10, 0.15)
DEFAULT_MAX_SHIFT_HOURS = 4
SHIFT_STRATEGY = "same_day_peak_to_lowest_load"


@dataclass(frozen=True)
class PeakShiftTable:
    """Metadata for the peak-shift simulation table."""

    table_name: str
    row_count: int
    max_peak_reduction: float
    energy_preserved_failures: int


def build_peak_shift_simulation(
    db_path: Path,
    flexible_load_percents: tuple[float, ...] = DEFAULT_FLEXIBLE_LOAD_PERCENTS,
    max_shift_hours: int = DEFAULT_MAX_SHIFT_HOURS,
) -> PeakShiftTable:
    """Build same-day peak-shifting simulation output."""

    with connect_duckdb(db_path) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
        connection.execute("DROP TABLE IF EXISTS gold.gold_peak_shift_simulation")
        values_clause = ", ".join(f"({value})" for value in flexible_load_percents)
        connection.execute(
            f"""
            CREATE TABLE gold.gold_peak_shift_simulation AS
            WITH flexible_load(flexible_load_percent) AS (
                VALUES {values_clause}
            ),
            daily_usage AS (
                SELECT
                    campus_id,
                    source_system,
                    meter_id,
                    building_id,
                    CAST(usage_hour AS DATE) AS simulation_date,
                    usage_hour,
                    SUM(total_consumption) AS hourly_consumption
                FROM gold.gold_hourly_electricity_usage
                GROUP BY campus_id, source_system, meter_id, building_id, simulation_date, usage_hour
            ),
            ranked AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY campus_id, source_system, meter_id, building_id, simulation_date
                        ORDER BY hourly_consumption DESC, usage_hour
                    ) AS peak_rank,
                    ROW_NUMBER() OVER (
                        PARTITION BY campus_id, source_system, meter_id, building_id, simulation_date
                        ORDER BY hourly_consumption ASC, usage_hour
                    ) AS low_rank,
                    SUM(hourly_consumption) OVER (
                        PARTITION BY campus_id, source_system, meter_id, building_id, simulation_date
                    ) AS baseline_daily_consumption
                FROM daily_usage
            ),
            peak_low AS (
                SELECT
                    peak.campus_id,
                    peak.source_system,
                    peak.meter_id,
                    peak.building_id,
                    peak.simulation_date,
                    peak.usage_hour AS peak_hour,
                    low.usage_hour AS target_hour,
                    peak.hourly_consumption AS baseline_peak_consumption,
                    low.hourly_consumption AS baseline_target_consumption,
                    peak.baseline_daily_consumption
                FROM ranked peak
                JOIN ranked low
                 ON peak.campus_id = low.campus_id
                 AND peak.source_system = low.source_system
                 AND peak.meter_id = low.meter_id
                 AND COALESCE(peak.building_id, -1) = COALESCE(low.building_id, -1)
                 AND peak.simulation_date = low.simulation_date
                WHERE peak.peak_rank = 1
                  AND low.low_rank = 1
                  AND peak.usage_hour != low.usage_hour
                  AND ABS(DATE_DIFF('hour', peak.usage_hour, low.usage_hour)) <= {max_shift_hours}
            ),
            simulated AS (
                SELECT
                    'peak_shift_' || campus_id || '_' || source_system || '_' ||
                        simulation_date || '_' || CAST(flexible_load_percent * 100 AS INTEGER)
                        AS simulation_id,
                    campus_id,
                    source_system,
                    meter_id,
                    building_id,
                    simulation_date,
                    '{SHIFT_STRATEGY}' AS shift_strategy,
                    flexible_load_percent,
                    {max_shift_hours} AS max_shift_hours,
                    peak_hour,
                    target_hour,
                    baseline_daily_consumption,
                    baseline_peak_consumption,
                    baseline_target_consumption,
                    LEAST(
                        baseline_peak_consumption * flexible_load_percent,
                        baseline_peak_consumption
                    ) AS shifted_consumption
                FROM peak_low
                CROSS JOIN flexible_load
            ),
            simulated_hourly AS (
                SELECT
                    *,
                    baseline_peak_consumption - shifted_consumption AS simulated_peak_hour_consumption,
                    baseline_target_consumption + shifted_consumption AS simulated_target_hour_consumption,
                    baseline_daily_consumption - baseline_peak_consumption - baseline_target_consumption
                        + (baseline_peak_consumption - shifted_consumption)
                        + (baseline_target_consumption + shifted_consumption)
                        AS simulated_daily_consumption
                FROM simulated
            )
            SELECT
                simulation_id,
                campus_id,
                source_system,
                meter_id,
                building_id,
                simulation_date,
                shift_strategy,
                flexible_load_percent,
                max_shift_hours,
                peak_hour,
                target_hour,
                baseline_daily_consumption,
                baseline_peak_consumption,
                baseline_target_consumption,
                shifted_consumption,
                GREATEST(
                    simulated_peak_hour_consumption,
                    simulated_target_hour_consumption
                ) AS simulated_peak_consumption,
                baseline_peak_consumption - GREATEST(
                    simulated_peak_hour_consumption,
                    simulated_target_hour_consumption
                ) AS peak_reduction,
                CASE
                    WHEN baseline_peak_consumption = 0 THEN NULL
                    ELSE (
                        baseline_peak_consumption - GREATEST(
                            simulated_peak_hour_consumption,
                            simulated_target_hour_consumption
                        )
                    ) / baseline_peak_consumption
                END AS peak_reduction_percent,
                simulated_daily_consumption,
                ABS(baseline_daily_consumption - simulated_daily_consumption) < 0.0001
                    AS total_energy_preserved,
                simulated_peak_hour_consumption < 0 OR simulated_target_hour_consumption < 0
                    AS negative_usage_created,
                'Hourly consumption is used as a peak-load proxy. Static emissions factor: same-day load shifting preserves total kWh, so estimated emissions are unchanged.' AS notes
            FROM simulated_hourly
            WHERE simulated_peak_hour_consumption >= 0
              AND simulated_target_hour_consumption >= 0
              AND baseline_peak_consumption >= GREATEST(
                    simulated_peak_hour_consumption,
                    simulated_target_hour_consumption
                  )
            """
        )
        row_count, max_peak_reduction, energy_failures = connection.execute(
            """
            SELECT
                COUNT(*),
                COALESCE(MAX(peak_reduction), 0),
                COUNT(*) FILTER (WHERE NOT total_energy_preserved OR negative_usage_created)
            FROM gold.gold_peak_shift_simulation
            """
        ).fetchone()

    return PeakShiftTable(
        table_name="gold.gold_peak_shift_simulation",
        row_count=int(row_count),
        max_peak_reduction=float(max_peak_reduction),
        energy_preserved_failures=int(energy_failures),
    )


def render_peak_shift_summary(table: PeakShiftTable, db_path: Path) -> str:
    """Render a short CLI summary."""

    return (
        f"Wrote peak-shift simulation to {db_path}\n"
        f"- {table.table_name}: {table.row_count} rows\n"
        f"- max peak reduction: {table.max_peak_reduction:,.4f}\n"
        f"- energy preservation failures: {table.energy_preserved_failures}"
    )


def write_peak_shift_report(table: PeakShiftTable, db_path: Path, output_path: Path) -> Path:
    """Write a markdown report for peak-shift simulation."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Peak-Shifting Simulation Report",
        "",
        "## Purpose",
        "",
        "This report confirms that an offline same-day peak-shifting simulation was run on hourly electricity usage.",
        "",
        "## What This Built",
        "",
        "- `gold.gold_peak_shift_simulation`",
        "- Flexible load scenarios for 5%, 10%, and 15%",
        "- Before and after peak hourly consumption as a load proxy",
        "- Peak reduction and peak reduction percent",
        "- Daily energy preservation flag",
        "",
        "## Why This Matters",
        "",
        "The simulator estimates whether flexible load shifting could reduce peak hourly consumption without changing total daily energy.",
        "",
        "## Emissions Limitation",
        "",
        "The project currently uses a static DCCEEW Victoria Scope 2 emissions factor. If total daily kWh is preserved, estimated emissions remain unchanged. The simulator does not claim emissions reduction.",
        "",
        "## Strategy",
        "",
        f"`{SHIFT_STRATEGY}` shifts load within each campus/source/meter/building day from a peak hour to the same day's lowest-load hour when the target is within the max shift window.",
        "",
        f"DuckDB database: `{db_path}`",
        "",
        "| Table | Rows | Max Peak Reduction | Energy Preservation Failures |",
        "| --- | ---: | ---: | ---: |",
        (
            f"| `{table.table_name}` | {table.row_count} | "
            f"{table.max_peak_reduction:.4f} | {table.energy_preserved_failures} |"
        ),
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for peak-shift simulation."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Run offline peak-shifting simulation.")
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument("--report-path", type=Path, default=Path("reports/peak_shift_report.md"))
    parser.add_argument("--max-shift-hours", type=int, default=DEFAULT_MAX_SHIFT_HOURS)
    args = parser.parse_args()

    table = build_peak_shift_simulation(args.db_path, max_shift_hours=args.max_shift_hours)
    print(render_peak_shift_summary(table, args.db_path))
    report_path = write_peak_shift_report(table, args.db_path, args.report_path)
    print(f"Wrote peak-shift report to {report_path}")


if __name__ == "__main__":
    main()
