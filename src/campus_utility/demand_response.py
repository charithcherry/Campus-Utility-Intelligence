"""Offline demand-response event simulation workflow."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from campus_utility.config import get_config
from campus_utility.database import connect_duckdb

DEFAULT_EVENT_DATE = "2020-01-15"
DEFAULT_START_HOUR = 15
DEFAULT_END_HOUR = 18
DEFAULT_TARGET_REDUCTION_PERCENT = 0.10
DEFAULT_FLEXIBLE_LOAD_PERCENT = 0.15
DEFAULT_REBOUND_WINDOW_HOURS = 3
SIMULATION_VERSION = "demand_response_peak_only_v1"


@dataclass(frozen=True)
class DemandResponseTable:
    """Metadata for demand-response simulation output."""

    table_name: str
    row_count: int
    events_meeting_target: int
    energy_preservation_failures: int
    negative_load_failures: int
    max_achieved_reduction: float


def build_demand_response_simulation(
    db_path: Path,
    event_date: str = DEFAULT_EVENT_DATE,
    start_hour: int = DEFAULT_START_HOUR,
    end_hour: int = DEFAULT_END_HOUR,
    target_reduction_percent: float = DEFAULT_TARGET_REDUCTION_PERCENT,
    flexible_load_percent: float = DEFAULT_FLEXIBLE_LOAD_PERCENT,
    rebound_window_hours: int = DEFAULT_REBOUND_WINDOW_HOURS,
) -> DemandResponseTable:
    """Build an offline demand-response event simulation."""

    if start_hour >= end_hour:
        raise ValueError("Demand-response start_hour must be before end_hour")
    if not 0 <= target_reduction_percent <= 1:
        raise ValueError("target_reduction_percent must be between 0 and 1")
    if not 0 <= flexible_load_percent <= 1:
        raise ValueError("flexible_load_percent must be between 0 and 1")
    if rebound_window_hours < 1:
        raise ValueError("rebound_window_hours must be at least 1")

    with connect_duckdb(db_path) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS gold")
        connection.execute("DROP TABLE IF EXISTS gold.gold_demand_response_simulation")
        connection.execute(
            """
            CREATE TABLE gold.gold_demand_response_simulation AS
            WITH event_usage AS (
                SELECT
                    campus_id,
                    source_system,
                    meter_id,
                    building_id,
                    CAST(? AS DATE) AS event_date,
                    SUM(total_consumption) AS baseline_event_consumption,
                    COUNT(*) AS event_hour_count
                FROM gold.gold_hourly_electricity_usage
                WHERE CAST(usage_hour AS DATE) = CAST(? AS DATE)
                  AND HOUR(usage_hour) >= ?
                  AND HOUR(usage_hour) < ?
                GROUP BY campus_id, source_system, meter_id, building_id
            ),
            rebound_usage AS (
                SELECT
                    campus_id,
                    source_system,
                    meter_id,
                    building_id,
                    SUM(total_consumption) AS baseline_rebound_consumption,
                    COUNT(*) AS rebound_hour_count
                FROM gold.gold_hourly_electricity_usage
                WHERE CAST(usage_hour AS DATE) = CAST(? AS DATE)
                  AND HOUR(usage_hour) >= ?
                  AND HOUR(usage_hour) < ?
                GROUP BY campus_id, source_system, meter_id, building_id
            ),
            simulated AS (
                SELECT
                    'demand_response_' || event.campus_id || '_' || event.source_system || '_' ||
                        event.event_date || '_' || CAST(? AS INTEGER) || '_' || CAST(? AS INTEGER)
                        AS simulation_id,
                    event.campus_id,
                    event.source_system,
                    event.meter_id,
                    event.building_id,
                    event.event_date,
                    ?::INTEGER AS start_hour,
                    ?::INTEGER AS end_hour,
                    (?::INTEGER - ?::INTEGER) AS event_duration_hours,
                    ?::DOUBLE AS target_reduction_percent,
                    ?::DOUBLE AS flexible_load_percent,
                    ?::INTEGER AS rebound_window_hours,
                    event.baseline_event_consumption,
                    COALESCE(rebound.baseline_rebound_consumption, 0) AS baseline_rebound_consumption,
                    event.baseline_event_consumption * ?::DOUBLE AS target_reduction,
                    LEAST(
                        event.baseline_event_consumption * ?::DOUBLE,
                        event.baseline_event_consumption
                    ) AS achieved_reduction,
                    event.baseline_event_consumption - LEAST(
                        event.baseline_event_consumption * ?::DOUBLE,
                        event.baseline_event_consumption
                    ) AS simulated_event_consumption,
                    COALESCE(rebound.baseline_rebound_consumption, 0)
                        + LEAST(
                            event.baseline_event_consumption * ?::DOUBLE,
                            event.baseline_event_consumption
                        ) AS simulated_rebound_consumption
                FROM event_usage event
                LEFT JOIN rebound_usage rebound
                 ON event.campus_id = rebound.campus_id
                 AND event.source_system = rebound.source_system
                 AND event.meter_id = rebound.meter_id
                 AND COALESCE(event.building_id, -1) = COALESCE(rebound.building_id, -1)
            )
            SELECT
                simulation_id,
                campus_id,
                source_system,
                meter_id,
                building_id,
                event_date,
                start_hour,
                end_hour,
                event_duration_hours,
                target_reduction_percent,
                flexible_load_percent,
                rebound_window_hours,
                baseline_event_consumption,
                simulated_event_consumption,
                target_reduction,
                achieved_reduction,
                GREATEST(target_reduction - achieved_reduction, 0) AS unmet_reduction,
                achieved_reduction >= target_reduction AS target_met,
                baseline_rebound_consumption,
                simulated_rebound_consumption,
                simulated_rebound_consumption - baseline_rebound_consumption AS rebound_load,
                ABS(
                    (baseline_event_consumption + baseline_rebound_consumption)
                    - (simulated_event_consumption + simulated_rebound_consumption)
                ) < 0.0001 AS total_energy_preserved,
                simulated_event_consumption < 0 OR simulated_rebound_consumption < 0
                    AS negative_load_created,
                CASE
                    WHEN target_reduction = 0 THEN NULL
                    ELSE achieved_reduction / target_reduction
                END AS target_achievement_ratio,
                NULL::DOUBLE AS estimated_emissions_impact_kg_co2e,
                'No emissions impact is calculated unless real time-varying carbon intensity is loaded.'
                    AS emissions_notes,
                ? AS simulation_version,
                'Offline simulation only. This is not real-time control or utility program participation.'
                    AS notes
            FROM simulated
            WHERE baseline_event_consumption > 0
            """,
            [
                event_date,
                event_date,
                start_hour,
                end_hour,
                event_date,
                end_hour,
                end_hour + rebound_window_hours,
                start_hour,
                end_hour,
                start_hour,
                end_hour,
                end_hour,
                start_hour,
                target_reduction_percent,
                flexible_load_percent,
                rebound_window_hours,
                target_reduction_percent,
                flexible_load_percent,
                flexible_load_percent,
                flexible_load_percent,
                SIMULATION_VERSION,
            ],
        )
        row_count, events_meeting_target, energy_failures, negative_failures, max_reduction = (
            connection.execute(
                """
                SELECT
                    COUNT(*),
                    COUNT(*) FILTER (WHERE target_met),
                    COUNT(*) FILTER (WHERE NOT total_energy_preserved),
                    COUNT(*) FILTER (WHERE negative_load_created),
                    COALESCE(MAX(achieved_reduction), 0)
                FROM gold.gold_demand_response_simulation
                """
            ).fetchone()
        )

    return DemandResponseTable(
        table_name="gold.gold_demand_response_simulation",
        row_count=int(row_count),
        events_meeting_target=int(events_meeting_target),
        energy_preservation_failures=int(energy_failures),
        negative_load_failures=int(negative_failures),
        max_achieved_reduction=float(max_reduction),
    )


def render_demand_response_summary(table: DemandResponseTable, db_path: Path) -> str:
    """Render a short CLI summary."""

    return (
        f"Wrote demand-response simulation to {db_path}\n"
        f"- {table.table_name}: {table.row_count} rows\n"
        f"- events meeting target: {table.events_meeting_target}\n"
        f"- energy preservation failures: {table.energy_preservation_failures}\n"
        f"- negative load failures: {table.negative_load_failures}\n"
        f"- max achieved reduction: {table.max_achieved_reduction:,.4f}"
    )


def write_demand_response_report(
    table: DemandResponseTable,
    db_path: Path,
    output_path: Path,
) -> Path:
    """Write a markdown report for demand-response simulation."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Demand-Response Event Simulation Report",
        "",
        "## Purpose",
        "",
        "This report confirms that an offline grid-stress event simulation was run against hourly electricity usage.",
        "",
        "## What This Built",
        "",
        "- `gold.gold_demand_response_simulation`",
        "- Event-window baseline and simulated load",
        "- Target reduction and achieved reduction",
        "- Unmet reduction",
        "- Rebound load after the event",
        "- Energy preservation and negative-load checks",
        "",
        "## Scenario Assumptions",
        "",
        f"- Default event date: `{DEFAULT_EVENT_DATE}`",
        f"- Default event window: `{DEFAULT_START_HOUR}:00` to `{DEFAULT_END_HOUR}:00`",
        f"- Default target reduction: `{DEFAULT_TARGET_REDUCTION_PERCENT:.0%}` of event-window usage",
        f"- Default flexible-load assumption: `{DEFAULT_FLEXIBLE_LOAD_PERCENT:.0%}` of event-window usage",
        f"- Default rebound window: `{DEFAULT_REBOUND_WINDOW_HOURS}` hours after the event",
        "",
        "## Why This Matters",
        "",
        "The simulator estimates whether flexible load could reduce electricity usage during a selected grid-stress event window while preserving energy through rebound load after the event.",
        "",
        "## Accuracy Notes",
        "",
        "- Offline simulation only.",
        "- Not real-time grid control.",
        "- Does not imply utility demand-response program participation.",
        "- Emissions impact is not calculated unless real time-varying carbon intensity is loaded.",
        "- If all simulated rows meet the target, that means the configured target was feasible under the assumed flexible-load percentage. It is not proof of real operational flexibility.",
        "",
        f"DuckDB database: `{db_path}`",
        "",
        "| Table | Rows | Events Meeting Target | Energy Failures | Negative Load Failures | Max Achieved Reduction |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| `{table.table_name}` | {table.row_count} | {table.events_meeting_target} | "
            f"{table.energy_preservation_failures} | {table.negative_load_failures} | "
            f"{table.max_achieved_reduction:.4f} |"
        ),
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for demand-response event simulation."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Run offline demand-response event simulation.")
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    parser.add_argument("--report-path", type=Path, default=Path("reports/demand_response_report.md"))
    parser.add_argument("--event-date", default=DEFAULT_EVENT_DATE)
    parser.add_argument("--start-hour", type=int, default=DEFAULT_START_HOUR)
    parser.add_argument("--end-hour", type=int, default=DEFAULT_END_HOUR)
    parser.add_argument("--target-reduction-percent", type=float, default=DEFAULT_TARGET_REDUCTION_PERCENT)
    parser.add_argument("--flexible-load-percent", type=float, default=DEFAULT_FLEXIBLE_LOAD_PERCENT)
    parser.add_argument("--rebound-window-hours", type=int, default=DEFAULT_REBOUND_WINDOW_HOURS)
    args = parser.parse_args()

    table = build_demand_response_simulation(
        args.db_path,
        event_date=args.event_date,
        start_hour=args.start_hour,
        end_hour=args.end_hour,
        target_reduction_percent=args.target_reduction_percent,
        flexible_load_percent=args.flexible_load_percent,
        rebound_window_hours=args.rebound_window_hours,
    )
    print(render_demand_response_summary(table, args.db_path))
    report_path = write_demand_response_report(table, args.db_path, args.report_path)
    print(f"Wrote demand-response report to {report_path}")


if __name__ == "__main__":
    main()
