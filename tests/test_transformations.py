import duckdb

from campus_utility.transformations import transform_silver_tables, write_transform_report


def test_transform_silver_tables_filters_invalid_rows_and_deduplicates(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    db_path.parent.mkdir()

    with duckdb.connect(str(db_path)) as connection:
        connection.execute("CREATE SCHEMA bronze")
        connection.execute(
            """
            CREATE TABLE bronze.bronze_building_consumption (
                campus_id BIGINT, meter_id BIGINT, timestamp TIMESTAMP, consumption DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO bronze.bronze_building_consumption VALUES
            (1, 10, '2024-01-01 00:00:00', 12.5),
            (1, 10, '2024-01-01 00:00:00', 12.5),
            (1, 10, '2024-01-01 00:15:00', -1.0)
            """
        )
        connection.execute(
            """
            CREATE TABLE bronze.bronze_nmi_consumption (
                campus_id VARCHAR, meter_id BIGINT, timestamp TIMESTAMP,
                consumption DOUBLE, demand_kW DOUBLE, demand_kVA DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO bronze.bronze_nmi_consumption VALUES
            ('1', 20, '2024-01-01 00:00:00', 50.0, 200.0, 210.0),
            ('N/A', 20, '2024-01-01 00:15:00', 50.0, 200.0, 210.0)
            """
        )
        connection.execute(
            """
            CREATE TABLE bronze.bronze_building_submeter_consumption (
                building_id BIGINT, id BIGINT, campus_id BIGINT, timestamp TIMESTAMP,
                consumption DOUBLE, current DOUBLE, voltage DOUBLE, power DOUBLE, power_factor DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO bronze.bronze_building_submeter_consumption VALUES
            (5, 30, 1, '2024-01-01 00:00:00', 4.0, 2.0, 240.0, 1.0, 0.95),
            (5, 30, 1, '2024-01-01 00:00:00', 4.0, 2.0, 240.0, 1.0, 0.95),
            (NULL, 30, 1, '2024-01-01 00:05:00', 4.0, 2.0, 240.0, 1.0, 0.95)
            """
        )

    tables = transform_silver_tables(db_path)

    assert {table.row_count for table in tables} == {1}

    with duckdb.connect(str(db_path)) as connection:
        building_rows = connection.execute(
            "SELECT campus_id, meter_id, consumption FROM silver.silver_building_electricity_readings"
        ).fetchall()
        nmi_rows = connection.execute(
            "SELECT campus_id, demand_kw FROM silver.silver_nmi_electricity_readings"
        ).fetchall()
        submeter_rows = connection.execute(
            "SELECT building_id, meter_id FROM silver.silver_submeter_electricity_readings"
        ).fetchall()

    assert building_rows == [(1, 10, 12.5)]
    assert nmi_rows == [(1, 200.0)]
    assert submeter_rows == [(5, 30)]


def test_write_transform_report_creates_markdown(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    report_path = tmp_path / "reports" / "silver_transform_report.md"
    db_path.parent.mkdir()

    with duckdb.connect(str(db_path)) as connection:
        connection.execute("CREATE SCHEMA bronze")
        connection.execute(
            "CREATE TABLE bronze.bronze_building_consumption AS SELECT 1 campus_id, 1 meter_id, "
            "CAST('2024-01-01' AS TIMESTAMP) AS timestamp, 1.0 consumption"
        )
        connection.execute(
            "CREATE TABLE bronze.bronze_nmi_consumption AS SELECT '1' campus_id, 1 meter_id, "
            "CAST('2024-01-01' AS TIMESTAMP) AS timestamp, 1.0 consumption, "
            "4.0 demand_kW, 4.5 demand_kVA"
        )
        connection.execute(
            "CREATE TABLE bronze.bronze_building_submeter_consumption AS SELECT 1 building_id, "
            "1 id, 1 campus_id, CAST('2024-01-01' AS TIMESTAMP) AS timestamp, 1.0 consumption, "
            "1.0 AS current, 240.0 AS voltage, 1.0 AS power, 0.9 AS power_factor"
        )

    tables = transform_silver_tables(db_path)
    write_transform_report(tables, db_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "Silver Transformation Report" in report
    assert "silver.silver_building_electricity_readings" in report
