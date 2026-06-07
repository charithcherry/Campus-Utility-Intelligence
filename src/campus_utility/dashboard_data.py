"""Data access helpers for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


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
            estimated_emissions_kg_co2e
        FROM gold.gold_electricity_emissions
        WHERE campus_id IN (SELECT UNNEST(?))
          AND source_system IN (SELECT UNNEST(?))
        ORDER BY usage_month, campus_id, source_system
        """,
        [campus_ids, source_systems],
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


def _query_dataframe(db_path: Path, sql: str, params: list[object]) -> pd.DataFrame:
    with duckdb.connect(str(db_path), read_only=True) as connection:
        return connection.execute(sql, params).fetchdf()
