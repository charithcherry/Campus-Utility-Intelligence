import duckdb

from campus_utility.dashboard_data import (
    get_filter_options,
    load_emissions,
    load_monthly_usage,
    load_peak_demand,
    load_reconciliation,
)


def test_dashboard_data_helpers_load_expected_frames(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_dashboard_test_database(db_path)

    campuses, sources = get_filter_options(db_path)
    usage = load_monthly_usage(db_path, campuses, sources)
    emissions = load_emissions(db_path, campuses, sources)
    peak = load_peak_demand(db_path, campuses)
    reconciliation = load_reconciliation(db_path, campuses)

    assert campuses == [1]
    assert sources == ["building_consumption"]
    assert usage["total_consumption"].sum() == 100.0
    assert emissions["estimated_emissions_kg_co2e"].sum() == 79.0
    assert peak["peak_demand_kw"].iloc[0] == 90.0
    assert reconciliation["consumption_difference"].iloc[0] == 20.0


def _create_dashboard_test_database(db_path):
    db_path.parent.mkdir(parents=True)
    with duckdb.connect(str(db_path)) as connection:
        connection.execute("CREATE SCHEMA gold")
        connection.execute(
            """
            CREATE TABLE gold.gold_monthly_electricity_usage (
                campus_id BIGINT,
                source_system VARCHAR,
                usage_month DATE,
                total_consumption DOUBLE,
                reading_count BIGINT,
                max_daily_meter_count BIGINT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_monthly_electricity_usage VALUES
            (1, 'building_consumption', '2024-01-01', 100.0, 10, 1)
            """
        )
        connection.execute(
            """
            CREATE TABLE gold.gold_electricity_emissions (
                campus_id BIGINT,
                source_system VARCHAR,
                usage_month DATE,
                total_consumption DOUBLE,
                emissions_factor_kg_co2e_per_unit DOUBLE,
                estimated_emissions_kg_co2e DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_electricity_emissions VALUES
            (1, 'building_consumption', '2024-01-01', 100.0, 0.79, 79.0)
            """
        )
        connection.execute(
            """
            CREATE TABLE gold.gold_peak_demand (
                campus_id BIGINT,
                meter_id BIGINT,
                peak_timestamp TIMESTAMP,
                peak_demand_kw DOUBLE,
                peak_demand_kva DOUBLE,
                consumption_at_peak DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_peak_demand VALUES
            (1, 20, '2024-01-01 00:00:00', 90.0, 95.0, 35.0)
            """
        )
        connection.execute(
            """
            CREATE TABLE gold.gold_monthly_nmi_building_reconciliation (
                campus_id BIGINT,
                usage_month DATE,
                nmi_consumption DOUBLE,
                building_consumption DOUBLE,
                consumption_difference DOUBLE,
                difference_ratio_to_nmi DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_monthly_nmi_building_reconciliation VALUES
            (1, '2024-01-01', 100.0, 80.0, 20.0, 0.2)
            """
        )
