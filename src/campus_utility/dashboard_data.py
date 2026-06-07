"""Data access helpers for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def table_exists(db_path: Path, schema_name: str, table_name: str) -> bool:
    """Return whether a DuckDB table exists."""

    with duckdb.connect(str(db_path), read_only=True) as connection:
        return bool(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = ?
                  AND table_name = ?
                """,
                [schema_name, table_name],
            ).fetchone()[0]
        )


def get_filter_options(db_path: Path) -> tuple[list[int], list[str]]:
    """Return campus and source options for dashboard filters."""

    with duckdb.connect(str(db_path), read_only=True) as connection:
        campuses = [
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT campus_id FROM gold.gold_monthly_electricity_usage ORDER BY campus_id"
            ).fetchall()
        ]
        sources = [
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT source_system FROM gold.gold_monthly_electricity_usage ORDER BY source_system"
            ).fetchall()
        ]
    return campuses, sources


def load_monthly_usage(db_path: Path, campus_ids: list[int], source_systems: list[str]) -> pd.DataFrame:
    """Load monthly usage for selected campuses and source systems."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            usage_month,
            campus_id,
            source_system,
            total_consumption
        FROM gold.gold_monthly_electricity_usage
        WHERE campus_id IN (SELECT UNNEST(?))
          AND source_system IN (SELECT UNNEST(?))
        ORDER BY usage_month, campus_id, source_system
        """,
        [campus_ids, source_systems],
    )


def load_executive_summary(db_path: Path, campus_ids: list[int], source_systems: list[str]) -> dict[str, float]:
    """Load top-level dashboard KPI values."""

    with duckdb.connect(str(db_path), read_only=True) as connection:
        usage = connection.execute(
            """
            WITH monthly AS (
                SELECT
                    usage_month,
                    SUM(total_consumption) AS monthly_consumption
                FROM gold.gold_monthly_electricity_usage
                WHERE campus_id IN (SELECT UNNEST(?))
                  AND source_system IN (SELECT UNNEST(?))
                GROUP BY usage_month
            ),
            ranked AS (
                SELECT
                    monthly_consumption,
                    ROW_NUMBER() OVER (ORDER BY usage_month DESC) AS month_rank
                FROM monthly
            )
            SELECT
                COALESCE(SUM(monthly_consumption), 0) AS total_consumption,
                COALESCE(MAX(monthly_consumption) FILTER (WHERE month_rank = 1), 0)
                    AS latest_month_consumption,
                COALESCE(MAX(monthly_consumption) FILTER (WHERE month_rank = 2), 0)
                    AS previous_month_consumption
            FROM ranked
            """,
            [campus_ids, source_systems],
        ).fetchone()
        emissions = connection.execute(
            """
            SELECT COALESCE(SUM(estimated_emissions_kg_co2e), 0)
            FROM gold.gold_electricity_emissions
            WHERE campus_id IN (SELECT UNNEST(?))
              AND source_system IN (SELECT UNNEST(?))
            """,
            [campus_ids, source_systems],
        ).fetchone()[0]
        peak = connection.execute(
            """
            SELECT COALESCE(MAX(peak_demand_kw), 0)
            FROM gold.gold_peak_demand
            WHERE campus_id IN (SELECT UNNEST(?))
            """,
            [campus_ids],
        ).fetchone()[0]

        high_usage_rate = 0.0
        if table_exists(db_path, "gold", "gold_weather_normalized_usage"):
            high_usage_rate = connection.execute(
                """
                SELECT
                    COALESCE(
                        COUNT(*) FILTER (WHERE is_high_usage_candidate)::DOUBLE
                        / NULLIF(COUNT(*), 0),
                        0
                    )
                FROM gold.gold_weather_normalized_usage
                WHERE campus_id IN (SELECT UNNEST(?))
                  AND source_system IN (SELECT UNNEST(?))
                """,
                [campus_ids, source_systems],
            ).fetchone()[0]

        best_peak_reduction = 0.0
        if table_exists(db_path, "gold", "gold_peak_shift_simulation"):
            best_peak_reduction = connection.execute(
                """
                SELECT COALESCE(MAX(peak_reduction), 0)
                FROM gold.gold_peak_shift_simulation
                WHERE campus_id IN (SELECT UNNEST(?))
                  AND source_system IN (SELECT UNNEST(?))
                """,
                [campus_ids, source_systems],
            ).fetchone()[0]

    latest_usage = float(usage[1])
    previous_usage = float(usage[2])
    usage_delta_percent = (
        (latest_usage - previous_usage) / previous_usage if previous_usage else 0.0
    )
    return {
        "total_consumption": float(usage[0]),
        "latest_month_consumption": latest_usage,
        "previous_month_consumption": previous_usage,
        "usage_delta_percent": usage_delta_percent,
        "estimated_emissions_kg_co2e": float(emissions),
        "peak_demand_kw": float(peak),
        "high_usage_rate": float(high_usage_rate),
        "best_peak_reduction": float(best_peak_reduction),
    }


def load_monthly_usage_by_campus(db_path: Path, campus_ids: list[int], source_systems: list[str]) -> pd.DataFrame:
    """Load monthly usage grouped by campus."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            usage_month,
            campus_id,
            SUM(total_consumption) AS total_consumption
        FROM gold.gold_monthly_electricity_usage
        WHERE campus_id IN (SELECT UNNEST(?))
          AND source_system IN (SELECT UNNEST(?))
        GROUP BY usage_month, campus_id
        ORDER BY usage_month, campus_id
        """,
        [campus_ids, source_systems],
    )


def load_hourly_usage_heatmap(db_path: Path, campus_ids: list[int], source_systems: list[str]) -> pd.DataFrame:
    """Load average usage by day of week and hour of day."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            DAYNAME(usage_hour) AS day_of_week,
            DAYOFWEEK(usage_hour) AS day_order,
            HOUR(usage_hour) AS hour_of_day,
            AVG(total_consumption) AS avg_consumption
        FROM gold.gold_hourly_electricity_usage
        WHERE campus_id IN (SELECT UNNEST(?))
          AND source_system IN (SELECT UNNEST(?))
        GROUP BY day_of_week, day_order, hour_of_day
        ORDER BY day_order, hour_of_day
        """,
        [campus_ids, source_systems],
    )


def load_top_usage_entities(
    db_path: Path, campus_ids: list[int], source_systems: list[str], limit: int = 20
) -> pd.DataFrame:
    """Load top meter/building groups by usage."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            campus_id,
            source_system,
            meter_id,
            building_id,
            SUM(total_consumption) AS total_consumption
        FROM gold.gold_hourly_electricity_usage
        WHERE campus_id IN (SELECT UNNEST(?))
          AND source_system IN (SELECT UNNEST(?))
        GROUP BY campus_id, source_system, meter_id, building_id
        ORDER BY total_consumption DESC
        LIMIT ?
        """,
        [campus_ids, source_systems, limit],
    )


def load_peak_demand(db_path: Path, campus_ids: list[int]) -> pd.DataFrame:
    """Load top peak-demand records for selected campuses."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            campus_id,
            meter_id,
            peak_timestamp,
            peak_demand_kw,
            peak_demand_kva
        FROM gold.gold_peak_demand
        WHERE campus_id IN (SELECT UNNEST(?))
        ORDER BY peak_demand_kw DESC
        LIMIT 20
        """,
        [campus_ids],
    )


def load_emissions(db_path: Path, campus_ids: list[int], source_systems: list[str]) -> pd.DataFrame:
    """Load monthly estimated emissions for selected campuses and sources."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            usage_month,
            campus_id,
            source_system,
            total_consumption,
            factor_id,
            factor_region,
            factor_year,
            emissions_factor_kg_co2e_per_kwh,
            factor_source_name,
            used_default_factor,
            estimated_emissions_kg_co2e
        FROM gold.gold_electricity_emissions
        WHERE campus_id IN (SELECT UNNEST(?))
          AND source_system IN (SELECT UNNEST(?))
        ORDER BY usage_month, campus_id, source_system
        """,
        [campus_ids, source_systems],
    )


def load_emissions_assumptions(db_path: Path) -> pd.DataFrame:
    """Load distinct emissions factor assumptions used in gold emissions."""

    return _query_dataframe(
        db_path,
        """
        SELECT DISTINCT
            factor_id,
            factor_region,
            factor_year,
            emissions_factor_kg_co2e_per_kwh,
            factor_source_name,
            factor_source_url,
            used_default_factor,
            factor_notes
        FROM gold.gold_electricity_emissions
        ORDER BY factor_region, factor_year, factor_id
        """,
        [],
    )


def load_reconciliation(db_path: Path, campus_ids: list[int]) -> pd.DataFrame:
    """Load monthly NMI/building reconciliation for selected campuses."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            usage_month,
            campus_id,
            nmi_consumption,
            building_consumption,
            consumption_difference,
            difference_ratio_to_nmi
        FROM gold.gold_monthly_nmi_building_reconciliation
        WHERE campus_id IN (SELECT UNNEST(?))
        ORDER BY ABS(consumption_difference) DESC NULLS LAST
        LIMIT 30
        """,
        [campus_ids],
    )


def load_weather_baseline_summary(db_path: Path, campus_ids: list[int]) -> pd.DataFrame:
    """Load high-usage candidate summary by campus and source."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            campus_id,
            source_system,
            COUNT(*) AS baseline_rows,
            COUNT(*) FILTER (WHERE is_high_usage_candidate) AS high_usage_candidates,
            COUNT(*) FILTER (WHERE is_high_usage_candidate)::DOUBLE / COUNT(*) AS high_usage_rate,
            AVG(residual_percent) AS avg_residual_percent,
            MAX(efficiency_opportunity_score) AS max_efficiency_opportunity_score
        FROM gold.gold_weather_normalized_usage
        WHERE campus_id IN (SELECT UNNEST(?))
        GROUP BY campus_id, source_system
        ORDER BY high_usage_rate DESC, high_usage_candidates DESC
        """,
        [campus_ids],
    )


def load_weather_actual_expected_trend(db_path: Path, campus_ids: list[int], source_systems: list[str]) -> pd.DataFrame:
    """Load monthly actual versus expected weather-normalized usage."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            DATE_TRUNC('month', usage_hour)::DATE AS usage_month,
            campus_id,
            source_system,
            SUM(actual_consumption) AS actual_consumption,
            SUM(expected_consumption) AS expected_consumption,
            SUM(residual_consumption) AS residual_consumption
        FROM gold.gold_weather_normalized_usage
        WHERE campus_id IN (SELECT UNNEST(?))
          AND source_system IN (SELECT UNNEST(?))
        GROUP BY usage_month, campus_id, source_system
        ORDER BY usage_month, campus_id, source_system
        """,
        [campus_ids, source_systems],
    )


def load_weather_candidate_rate_trend(db_path: Path, campus_ids: list[int], source_systems: list[str]) -> pd.DataFrame:
    """Load monthly high-usage candidate rates."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            DATE_TRUNC('month', usage_hour)::DATE AS usage_month,
            campus_id,
            source_system,
            COUNT(*) AS baseline_rows,
            COUNT(*) FILTER (WHERE is_high_usage_candidate) AS high_usage_candidates,
            COUNT(*) FILTER (WHERE is_high_usage_candidate)::DOUBLE / COUNT(*) AS high_usage_rate
        FROM gold.gold_weather_normalized_usage
        WHERE campus_id IN (SELECT UNNEST(?))
          AND source_system IN (SELECT UNNEST(?))
        GROUP BY usage_month, campus_id, source_system
        ORDER BY usage_month, campus_id, source_system
        """,
        [campus_ids, source_systems],
    )


def load_temperature_usage_sample(
    db_path: Path, campus_ids: list[int], source_systems: list[str], limit: int = 5000
) -> pd.DataFrame:
    """Load a bounded temperature versus usage sample."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            campus_id,
            source_system,
            usage_hour,
            air_temperature,
            actual_consumption
        FROM gold.gold_weather_normalized_usage
        WHERE campus_id IN (SELECT UNNEST(?))
          AND source_system IN (SELECT UNNEST(?))
          AND air_temperature IS NOT NULL
        ORDER BY usage_hour
        LIMIT ?
        """,
        [campus_ids, source_systems, limit],
    )


def load_top_weather_baseline_candidates(db_path: Path, campus_ids: list[int]) -> pd.DataFrame:
    """Load top weather-normalized high-usage candidates."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            campus_id,
            source_system,
            meter_id,
            building_id,
            usage_hour,
            actual_consumption,
            expected_consumption,
            residual_consumption,
            residual_percent,
            efficiency_opportunity_score
        FROM gold.gold_weather_normalized_usage
        WHERE campus_id IN (SELECT UNNEST(?))
          AND is_high_usage_candidate
        ORDER BY efficiency_opportunity_score DESC, residual_consumption DESC
        LIMIT 50
        """,
        [campus_ids],
    )


def load_peak_shift_summary(db_path: Path, campus_ids: list[int], flexible_load_percent: float) -> pd.DataFrame:
    """Load peak-shift simulation summary by campus and source."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            campus_id,
            source_system,
            COUNT(*) AS simulation_rows,
            AVG(baseline_peak_consumption) AS avg_baseline_peak_consumption,
            AVG(simulated_peak_consumption) AS avg_simulated_peak_consumption,
            AVG(peak_reduction) AS avg_peak_reduction,
            AVG(peak_reduction_percent) AS avg_peak_reduction_percent,
            COUNT(*) FILTER (WHERE total_energy_preserved) AS energy_preserved_rows
        FROM gold.gold_peak_shift_simulation
        WHERE campus_id IN (SELECT UNNEST(?))
          AND flexible_load_percent = ?
        GROUP BY campus_id, source_system
        ORDER BY avg_peak_reduction DESC
        """,
        [campus_ids, flexible_load_percent],
    )


def load_peak_shift_scenario_comparison(db_path: Path, campus_ids: list[int], source_systems: list[str]) -> pd.DataFrame:
    """Load peak-shift comparison across flexible load percentages."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            flexible_load_percent,
            COUNT(*) AS valid_scenarios,
            AVG(peak_reduction) AS avg_peak_reduction,
            AVG(peak_reduction_percent) AS avg_peak_reduction_percent,
            MAX(peak_reduction) AS best_peak_reduction,
            COUNT(*) FILTER (WHERE NOT total_energy_preserved) AS energy_preservation_failures,
            COUNT(*) FILTER (WHERE negative_usage_created) AS negative_usage_rows,
            COUNT(*) FILTER (WHERE peak_reduction < 0) AS worse_peak_rows
        FROM gold.gold_peak_shift_simulation
        WHERE campus_id IN (SELECT UNNEST(?))
          AND source_system IN (SELECT UNNEST(?))
        GROUP BY flexible_load_percent
        ORDER BY flexible_load_percent
        """,
        [campus_ids, source_systems],
    )


def load_top_peak_shift_results(db_path: Path, campus_ids: list[int], flexible_load_percent: float) -> pd.DataFrame:
    """Load top peak-shift simulation results."""

    return _query_dataframe(
        db_path,
        """
        SELECT
            campus_id,
            source_system,
            meter_id,
            building_id,
            simulation_date,
            flexible_load_percent,
            baseline_peak_consumption,
            simulated_peak_consumption,
            peak_reduction,
            peak_reduction_percent,
            total_energy_preserved,
            notes
        FROM gold.gold_peak_shift_simulation
        WHERE campus_id IN (SELECT UNNEST(?))
          AND flexible_load_percent = ?
        ORDER BY peak_reduction DESC
        LIMIT 50
        """,
        [campus_ids, flexible_load_percent],
    )


def load_pipeline_row_counts(db_path: Path) -> pd.DataFrame:
    """Load row counts for bronze, silver, gold, and reference tables."""

    with duckdb.connect(str(db_path), read_only=True) as connection:
        tables = connection.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema IN ('bronze', 'silver', 'gold', 'reference')
            ORDER BY table_schema, table_name
            """
        ).fetchall()
        rows = [
            {
                "schema_name": schema,
                "table_name": table,
                "row_count": connection.execute(
                    f"SELECT COUNT(*) FROM {schema}.{table}"
                ).fetchone()[0],
            }
            for schema, table in tables
        ]
    return pd.DataFrame(rows)


def load_quality_check_summary(db_path: Path) -> pd.DataFrame:
    """Return status counts from the quality report table when available."""

    if not table_exists(db_path, "quality", "quality_check_results"):
        return pd.DataFrame()
    return _query_dataframe(
        db_path,
        """
        SELECT
            status,
            COUNT(*) AS check_count
        FROM quality.quality_check_results
        GROUP BY status
        ORDER BY status
        """,
        [],
    )


def _query_dataframe(db_path: Path, sql: str, params: list[object]) -> pd.DataFrame:
    with duckdb.connect(str(db_path), read_only=True) as connection:
        return connection.execute(sql, params).fetchdf()
