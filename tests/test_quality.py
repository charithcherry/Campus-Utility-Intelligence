import duckdb

from campus_utility.quality import run_quality_checks, write_quality_report


def test_run_quality_checks_passes_clean_silver_tables(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_quality_test_database(db_path)

    checks = run_quality_checks(db_path)

    assert checks
    assert {check.status for check in checks} == {"PASS"}


def test_run_quality_checks_flags_duplicate_keys(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_quality_test_database(db_path)

    with duckdb.connect(str(db_path)) as connection:
        connection.execute(
            """
            INSERT INTO silver.silver_building_electricity_readings VALUES
            (1, 10, '2024-01-01 00:00:00', 12.5, 'building_consumption')
            """
        )

    checks = run_quality_checks(db_path)
    duplicate_check = next(
        check
        for check in checks
        if check.table_name == "silver.silver_building_electricity_readings"
        and check.name == "duplicate_key_count"
    )

    assert duplicate_check.status == "FAIL"
    assert duplicate_check.observed_value == 1


def test_write_quality_report_creates_markdown(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    report_path = tmp_path / "reports" / "data_quality_report.md"
    _create_quality_test_database(db_path)
    checks = run_quality_checks(db_path)

    write_quality_report(checks, db_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "Data Quality Report" in report
    assert "required_fields_not_null" in report


def _create_quality_test_database(db_path):
    db_path.parent.mkdir(parents=True)
    with duckdb.connect(str(db_path)) as connection:
        connection.execute("CREATE SCHEMA bronze")
        connection.execute("CREATE TABLE bronze.bronze_campus_meta (id BIGINT, name VARCHAR)")
        connection.execute("INSERT INTO bronze.bronze_campus_meta VALUES (1, 'Campus A')")

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
            (1, 10, '2024-01-01 00:00:00', 12.5, 'building_consumption')
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
            (1, 20, '2024-01-01 00:00:00', 20.0, 80.0, 90.0, 'nmi_consumption')
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
