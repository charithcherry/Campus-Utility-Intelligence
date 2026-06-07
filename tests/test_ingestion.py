import duckdb
import pytest

from campus_utility.ingestion import ingest_raw_files, table_name_from_path, write_ingestion_report


def test_table_name_from_path_sanitizes_file_stem(tmp_path):
    path = tmp_path / "Building Consumption.csv"

    assert table_name_from_path(path) == "bronze_building_consumption"


def test_ingest_raw_files_loads_supported_csvs(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    (raw_dir / "building_consumption.csv").write_text(
        "campus_id,meter_id,timestamp,consumption\n"
        "1,10,2024-01-01 00:00:00,12.5\n"
        "1,10,2024-01-01 00:15:00,13.0\n",
        encoding="utf-8",
    )

    tables = ingest_raw_files(raw_dir, db_path)

    assert len(tables) == 1
    assert tables[0].table_name == "bronze.bronze_building_consumption"
    assert tables[0].row_count == 2
    assert tables[0].column_count == 4

    with duckdb.connect(str(db_path)) as connection:
        row_count = connection.execute(
            "SELECT COUNT(*) FROM bronze.bronze_building_consumption"
        ).fetchone()[0]

    assert row_count == 2


def test_ingest_raw_files_fails_when_no_raw_files(tmp_path):
    with pytest.raises(FileNotFoundError, match="No supported raw files"):
        ingest_raw_files(tmp_path / "raw", tmp_path / "processed" / "campus_utility.duckdb")


def test_write_ingestion_report_creates_markdown_summary(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    report_path = tmp_path / "reports" / "bronze_ingestion_report.md"
    (raw_dir / "building_consumption.csv").write_text(
        "campus_id,meter_id,timestamp,consumption\n"
        "1,10,2024-01-01 00:00:00,12.5\n",
        encoding="utf-8",
    )
    tables = ingest_raw_files(raw_dir, db_path)

    write_ingestion_report(tables, db_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "Bronze Ingestion Report" in report
    assert "bronze.bronze_building_consumption" in report
    assert "1 | 4" in report
