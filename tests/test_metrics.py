import duckdb

from campus_utility.metrics import build_gold_metrics, write_metrics_report


def test_build_gold_metrics_creates_usage_and_peak_tables(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_metrics_test_database(db_path)

    tables = build_gold_metrics(db_path)

    assert {table.table_name for table in tables} == {
        "gold.gold_hourly_electricity_usage",
        "gold.gold_daily_electricity_usage",
        "gold.gold_monthly_electricity_usage",
        "gold.gold_peak_demand",
    }

    with duckdb.connect(str(db_path)) as connection:
        hourly = connection.execute(
            """
            SELECT source_system, total_consumption, reading_count
            FROM gold.gold_hourly_electricity_usage
            WHERE source_system = 'building_consumption'
            """
        ).fetchall()
        peak = connection.execute(
            """
            SELECT campus_id, meter_id, peak_demand_kw
            FROM gold.gold_peak_demand
            """
        ).fetchall()

    assert hourly == [("building_consumption", 25.0, 2)]
    assert peak == [(1, 20, 90.0)]


def test_write_metrics_report_creates_markdown(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    report_path = tmp_path / "reports" / "gold_metrics_report.md"
    _create_metrics_test_database(db_path)
    tables = build_gold_metrics(db_path)

    write_metrics_report(tables, db_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "Gold Metrics Report" in report
    assert "gold.gold_peak_demand" in report


def _create_metrics_test_database(db_path):
    db_path.parent.mkdir(parents=True)
    with duckdb.connect(str(db_path)) as connection:
        connection.execute("CREATE SCHEMA silver")
        connection.execute(
            """
            CREATE TABLE silver.silver_building_electricity_readings (
                campus_id BIGINT,
                meter_id BIGINT,
                reading_timestamp TIMESTAMP,
                consumption DOUBLE,
                source_system VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO silver.silver_building_electricity_readings VALUES
            (1, 10, '2024-01-01 00:00:00', 12.5, 'building_consumption'),
            (1, 10, '2024-01-01 00:15:00', 12.5, 'building_consumption')
            """
        )
        connection.execute(
            """
            CREATE TABLE silver.silver_nmi_electricity_readings (
                campus_id BIGINT,
                meter_id BIGINT,
                reading_timestamp TIMESTAMP,
                consumption DOUBLE,
                demand_kw DOUBLE,
                demand_kva DOUBLE,
                source_system VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO silver.silver_nmi_electricity_readings VALUES
            (1, 20, '2024-01-01 00:00:00', 30.0, 80.0, 85.0, 'nmi_consumption'),
            (1, 20, '2024-01-01 00:15:00', 35.0, 90.0, 95.0, 'nmi_consumption')
            """
        )
        connection.execute(
            """
            CREATE TABLE silver.silver_submeter_electricity_readings (
                campus_id BIGINT,
                building_id BIGINT,
                meter_id BIGINT,
                reading_timestamp TIMESTAMP,
                consumption DOUBLE,
                current DOUBLE,
                voltage DOUBLE,
                power DOUBLE,
                power_factor DOUBLE,
                source_system VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO silver.silver_submeter_electricity_readings VALUES
            (1, 5, 30, '2024-01-01 00:00:00', 4.0, 2.0, 240.0, 1.0, 0.95,
             'building_submeter_consumption')
            """
        )
