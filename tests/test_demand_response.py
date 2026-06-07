import duckdb
import pytest

from campus_utility.demand_response import (
    build_demand_response_simulation,
    write_demand_response_report,
)


def test_build_demand_response_simulation_meets_target_and_preserves_energy(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_demand_response_test_database(db_path)

    table = build_demand_response_simulation(
        db_path,
        event_date="2024-01-01",
        start_hour=15,
        end_hour=17,
        target_reduction_percent=0.10,
        flexible_load_percent=0.20,
        rebound_window_hours=2,
    )

    assert table.table_name == "gold.gold_demand_response_simulation"
    assert table.row_count == 1
    assert table.events_meeting_target == 1
    assert table.energy_preservation_failures == 0
    assert table.negative_load_failures == 0

    with duckdb.connect(str(db_path)) as connection:
        row = connection.execute(
            """
            SELECT
                baseline_event_consumption,
                simulated_event_consumption,
                target_reduction,
                achieved_reduction,
                unmet_reduction,
                target_met,
                rebound_load,
                total_energy_preserved,
                estimated_emissions_impact_kg_co2e
            FROM gold.gold_demand_response_simulation
            """
        ).fetchone()

    assert row == (300.0, 240.0, 30.0, 60.0, 0.0, True, 60.0, True, None)


def test_build_demand_response_simulation_tracks_unmet_target(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_demand_response_test_database(db_path)

    table = build_demand_response_simulation(
        db_path,
        event_date="2024-01-01",
        start_hour=15,
        end_hour=17,
        target_reduction_percent=0.50,
        flexible_load_percent=0.10,
        rebound_window_hours=2,
    )

    assert table.events_meeting_target == 0

    with duckdb.connect(str(db_path)) as connection:
        row = connection.execute(
            """
            SELECT target_reduction, achieved_reduction, unmet_reduction, target_met
            FROM gold.gold_demand_response_simulation
            """
        ).fetchone()

    assert row == (150.0, 30.0, 120.0, False)


def test_build_demand_response_simulation_validates_event_window(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"

    with pytest.raises(ValueError, match="start_hour must be before end_hour"):
        build_demand_response_simulation(db_path, start_hour=18, end_hour=18)


def test_write_demand_response_report_creates_markdown(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    report_path = tmp_path / "reports" / "demand_response_report.md"
    _create_demand_response_test_database(db_path)
    table = build_demand_response_simulation(
        db_path,
        event_date="2024-01-01",
        start_hour=15,
        end_hour=17,
        target_reduction_percent=0.10,
        flexible_load_percent=0.20,
        rebound_window_hours=2,
    )

    write_demand_response_report(table, db_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "Demand-Response Event Simulation Report" in report
    assert "Not real-time grid control" in report


def _create_demand_response_test_database(db_path):
    db_path.parent.mkdir(parents=True)
    with duckdb.connect(str(db_path)) as connection:
        connection.execute("CREATE SCHEMA gold")
        connection.execute(
            """
            CREATE TABLE gold.gold_hourly_electricity_usage (
                campus_id BIGINT,
                source_system VARCHAR,
                meter_id BIGINT,
                building_id BIGINT,
                usage_hour TIMESTAMP,
                total_consumption DOUBLE,
                reading_count BIGINT,
                first_reading_timestamp TIMESTAMP,
                last_reading_timestamp TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_hourly_electricity_usage VALUES
            (1, 'building_consumption', 10, NULL, '2024-01-01 15:00:00', 100.0, 1,
             '2024-01-01 15:00:00', '2024-01-01 15:00:00'),
            (1, 'building_consumption', 10, NULL, '2024-01-01 16:00:00', 200.0, 1,
             '2024-01-01 16:00:00', '2024-01-01 16:00:00'),
            (1, 'building_consumption', 10, NULL, '2024-01-01 17:00:00', 50.0, 1,
             '2024-01-01 17:00:00', '2024-01-01 17:00:00'),
            (1, 'building_consumption', 10, NULL, '2024-01-01 18:00:00', 60.0, 1,
             '2024-01-01 18:00:00', '2024-01-01 18:00:00')
            """
        )
