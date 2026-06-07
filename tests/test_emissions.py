import duckdb

from campus_utility.emissions import build_emissions_metrics, write_emissions_report


def test_build_emissions_metrics_creates_estimates(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_emissions_test_database(db_path)

    table = build_emissions_metrics(db_path, emissions_factor=0.5)

    assert table.table_name == "gold.gold_electricity_emissions"
    assert table.row_count == 1
    assert table.emissions_factor == 0.5

    with duckdb.connect(str(db_path)) as connection:
        rows = connection.execute(
            """
            SELECT total_consumption, emissions_factor_kg_co2e_per_unit,
                   estimated_emissions_kg_co2e
            FROM gold.gold_electricity_emissions
            """
        ).fetchall()

    assert rows == [(100.0, 0.5, 50.0)]


def test_write_emissions_report_creates_markdown(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    report_path = tmp_path / "reports" / "emissions_metrics_report.md"
    _create_emissions_test_database(db_path)
    table = build_emissions_metrics(db_path, emissions_factor=0.5)

    write_emissions_report(table, db_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "Emissions Metrics Report" in report
    assert "0.5" in report


def _create_emissions_test_database(db_path):
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
