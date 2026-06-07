from pathlib import Path

import pandas as pd

from campus_utility.profiling import (
    detect_timestamp_coverage,
    discover_raw_files,
    profile_dataframe,
    render_profile_report,
    write_profile_report,
)


def test_discover_raw_files_returns_supported_files(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    csv_path = raw_dir / "electricity.csv"
    ignored_path = raw_dir / "notes.txt"
    csv_path.write_text("timestamp,kwh\n2024-01-01 00:00:00,12.5\n", encoding="utf-8")
    ignored_path.write_text("not data", encoding="utf-8")

    assert discover_raw_files(raw_dir) == [csv_path]


def test_profile_dataframe_summarizes_columns_duplicates_and_timestamps():
    dataframe = pd.DataFrame(
        {
            "timestamp": ["2024-01-01 00:00:00", "2024-01-01 01:00:00", "2024-01-01 01:00:00"],
            "building": ["A", "B", "B"],
            "kwh": [10.0, None, None],
        }
    )

    profile = profile_dataframe(Path("electricity.csv"), dataframe)

    assert profile.row_count == 3
    assert profile.column_count == 3
    assert profile.duplicate_count == 1
    assert profile.columns[2].null_count == 2
    assert profile.timestamp_coverage["timestamp"][0].startswith("2024-01-01 00:00:00")
    assert profile.timestamp_coverage["timestamp"][1].startswith("2024-01-01 01:00:00")


def test_detect_timestamp_coverage_ignores_unparseable_timestamp_columns():
    dataframe = pd.DataFrame({"timestamp_label": ["missing", "unknown"], "value": [1, 2]})

    assert detect_timestamp_coverage(dataframe) == {}


def test_render_profile_report_handles_no_files(tmp_path):
    report = render_profile_report(tmp_path / "raw", [])

    assert "No supported raw data files were found." in report
    assert "make profile" in report


def test_write_profile_report_creates_no_data_report(tmp_path):
    report_path = tmp_path / "reports" / "profile_report.md"

    write_profile_report(tmp_path / "raw", report_path)

    assert report_path.exists()
    assert "No supported raw data files were found." in report_path.read_text(encoding="utf-8")
