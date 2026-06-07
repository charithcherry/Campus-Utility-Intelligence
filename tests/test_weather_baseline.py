import duckdb

from campus_utility.weather_baseline import build_weather_baseline, write_baseline_report


def test_build_weather_baseline_calculates_residuals_and_scores(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_baseline_test_database(db_path)

    table = build_weather_baseline(db_path)

    assert table.table_name == "gold.gold_weather_normalized_usage"
    assert table.row_count == 3
    assert table.high_usage_candidate_count == 1

    with duckdb.connect(str(db_path)) as connection:
        rows = connection.execute(
            """
            SELECT actual_consumption, expected_consumption, residual_consumption,
                   residual_percent, is_high_usage_candidate, efficiency_opportunity_score
            FROM gold.gold_weather_normalized_usage
            ORDER BY actual_consumption
            """
        ).fetchall()

    assert rows[0] == (100.0, 100.0, 0.0, 0.0, False, 0.0)
    assert rows[2] == (200.0, 100.0, 100.0, 1.0, True, 100.0)


def test_write_baseline_report_creates_markdown(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    report_path = tmp_path / "reports" / "weather_baseline_report.md"
    _create_baseline_test_database(db_path)
    table = build_weather_baseline(db_path)

    write_baseline_report(table, db_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "Weather-Normalized Baseline Report" in report
    assert "gold.gold_weather_normalized_usage" in report


def _create_baseline_test_database(db_path):
    db_path.parent.mkdir(parents=True)
    with duckdb.connect(str(db_path)) as connection:
        connection.execute("CREATE SCHEMA bronze")
        connection.execute(
            """
            CREATE TABLE bronze.bronze_weather_data (
                campus_id BIGINT,
                timestamp TIMESTAMP,
                apparent_temperature DOUBLE,
                air_temperature DOUBLE,
                dew_point_temperature DOUBLE,
                relative_humidity DOUBLE,
                wind_speed VARCHAR,
                wind_direction VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO bronze.bronze_weather_data VALUES
            (1, '2024-01-01 08:00:00', 20.0, 20.0, 10.0, 60.0, '1.0', '90'),
            (1, '2024-01-08 08:00:00', 20.0, 20.0, 10.0, 60.0, '1.0', '90'),
            (1, '2024-01-15 08:00:00', 20.0, 20.0, 10.0, 60.0, '1.0', '90')
            """
        )
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
            (1, 'building_consumption', 10, NULL, '2024-01-01 08:00:00', 100.0, 4,
             '2024-01-01 08:00:00', '2024-01-01 08:45:00'),
            (1, 'building_consumption', 10, NULL, '2024-01-08 08:00:00', 100.0, 4,
             '2024-01-08 08:00:00', '2024-01-08 08:45:00'),
            (1, 'building_consumption', 10, NULL, '2024-01-15 08:00:00', 200.0, 4,
             '2024-01-15 08:00:00', '2024-01-15 08:45:00')
            """
        )
