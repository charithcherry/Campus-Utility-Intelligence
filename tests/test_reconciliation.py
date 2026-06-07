import duckdb

from campus_utility.reconciliation import build_reconciliation_tables, write_reconciliation_report


def test_build_reconciliation_tables_compares_nmi_and_building_usage(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_reconciliation_test_database(db_path)

    tables = build_reconciliation_tables(db_path)

    assert {table.table_name for table in tables} == {
        "gold.gold_daily_nmi_building_reconciliation",
        "gold.gold_monthly_nmi_building_reconciliation",
    }

    with duckdb.connect(str(db_path)) as connection:
        daily = connection.execute(
            """
            SELECT nmi_consumption, building_consumption, consumption_difference,
                   difference_ratio_to_nmi
            FROM gold.gold_daily_nmi_building_reconciliation
            """
        ).fetchall()

    assert daily == [(100.0, 80.0, 20.0, 0.2)]


def test_write_reconciliation_report_creates_markdown(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    report_path = tmp_path / "reports" / "reconciliation_report.md"
    _create_reconciliation_test_database(db_path)
    tables = build_reconciliation_tables(db_path)

    write_reconciliation_report(tables, db_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "NMI Building Reconciliation Report" in report
    assert "gold.gold_daily_nmi_building_reconciliation" in report


def _create_reconciliation_test_database(db_path):
    db_path.parent.mkdir(parents=True)
    with duckdb.connect(str(db_path)) as connection:
        connection.execute("CREATE SCHEMA gold")
        connection.execute(
            """
            CREATE TABLE gold.gold_daily_electricity_usage (
                campus_id BIGINT,
                source_system VARCHAR,
                usage_date DATE,
                total_consumption DOUBLE,
                reading_count BIGINT,
                meter_count BIGINT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_daily_electricity_usage VALUES
            (1, 'nmi_consumption', '2024-01-01', 100.0, 4, 1),
            (1, 'building_consumption', '2024-01-01', 80.0, 4, 2)
            """
        )
