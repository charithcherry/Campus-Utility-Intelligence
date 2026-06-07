import duckdb

from campus_utility.analytics import run_analytics_queries, write_analytics_report


def test_run_analytics_queries_writes_markdown_outputs(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    query_dir = tmp_path / "sql"
    output_dir = tmp_path / "reports" / "sql_analytics"
    _create_analytics_test_database(db_path)
    query_dir.mkdir()
    (query_dir / "sample.sql").write_text(
        "SELECT source_system, total_consumption FROM gold.gold_monthly_electricity_usage;",
        encoding="utf-8",
    )

    results = run_analytics_queries(db_path, query_dir, output_dir)

    assert len(results) == 1
    assert results[0].row_count == 1
    assert (output_dir / "sample.md").exists()


def test_write_analytics_report_creates_index(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    query_dir = tmp_path / "sql"
    output_dir = tmp_path / "reports" / "sql_analytics"
    report_path = tmp_path / "reports" / "sql_analytics_report.md"
    _create_analytics_test_database(db_path)
    query_dir.mkdir()
    (query_dir / "sample.sql").write_text(
        "SELECT source_system, total_consumption FROM gold.gold_monthly_electricity_usage;",
        encoding="utf-8",
    )
    results = run_analytics_queries(db_path, query_dir, output_dir)

    write_analytics_report(results, report_path)

    assert "SQL Analytics Report" in report_path.read_text(encoding="utf-8")


def _create_analytics_test_database(db_path):
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
