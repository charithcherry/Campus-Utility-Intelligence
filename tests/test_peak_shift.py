import duckdb

from campus_utility.peak_shift import build_peak_shift_simulation, write_peak_shift_report


def test_build_peak_shift_simulation_preserves_energy_and_reduces_peak(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_peak_shift_test_database(db_path)

    table = build_peak_shift_simulation(db_path, flexible_load_percents=(0.10,), max_shift_hours=4)

    assert table.table_name == "gold.gold_peak_shift_simulation"
    assert table.row_count == 1
    assert table.energy_preserved_failures == 0

    with duckdb.connect(str(db_path)) as connection:
        rows = connection.execute(
            """
            SELECT baseline_peak_consumption, simulated_peak_consumption, peak_reduction,
                   peak_reduction_percent, total_energy_preserved, negative_usage_created
            FROM gold.gold_peak_shift_simulation
            """
        ).fetchall()

    assert rows == [(100.0, 90.0, 10.0, 0.1, True, False)]


def test_build_peak_shift_simulation_respects_same_day_shift_window(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_peak_shift_test_database(db_path)

    table = build_peak_shift_simulation(db_path, flexible_load_percents=(0.10,), max_shift_hours=1)

    assert table.row_count == 0


def test_write_peak_shift_report_creates_markdown(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    report_path = tmp_path / "reports" / "peak_shift_report.md"
    _create_peak_shift_test_database(db_path)
    table = build_peak_shift_simulation(db_path, flexible_load_percents=(0.10,), max_shift_hours=4)

    write_peak_shift_report(table, db_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "Peak-Shifting Simulation Report" in report
    assert "emissions remain unchanged" in report


def _create_peak_shift_test_database(db_path):
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
            (1, 'building_consumption', 10, NULL, '2024-01-01 08:00:00', 100.0, 1,
             '2024-01-01 08:00:00', '2024-01-01 08:00:00'),
            (1, 'building_consumption', 10, NULL, '2024-01-01 10:00:00', 20.0, 1,
             '2024-01-01 10:00:00', '2024-01-01 10:00:00')
            """
        )
