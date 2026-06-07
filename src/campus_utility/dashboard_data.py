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


def _query_dataframe(db_path: Path, sql: str, params: list[object]) -> pd.DataFrame:
    with duckdb.connect(str(db_path), read_only=True) as connection:
        return connection.execute(sql, params).fetchdf()
