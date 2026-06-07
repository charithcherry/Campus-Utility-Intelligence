import duckdb
import pytest

from campus_utility.carbon_intensity import (
    build_time_varying_emissions,
    load_grid_carbon_intensity,
    write_carbon_intensity_report,
)


def test_load_grid_carbon_intensity_validates_required_columns(tmp_path):
    intensity_path = tmp_path / "bad_intensity.csv"
    intensity_path.write_text("region_code,region_name\nVIC1,Victoria\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        load_grid_carbon_intensity(intensity_path)


def test_load_grid_carbon_intensity_rejects_negative_values(tmp_path):
    intensity_path = tmp_path / "grid_carbon_intensity.csv"
    _write_intensity_file(
        intensity_path,
        rows=[
            "VIC1,Victoria,2024-01-01 08:00:00,2024-01-01 09:00:00,-0.10,Synthetic test fixture,,test,synthetic test row",
        ],
    )

    with pytest.raises(ValueError, match="negative emissions intensity"):
        load_grid_carbon_intensity(intensity_path)


def test_load_grid_carbon_intensity_rejects_duplicate_region_hours(tmp_path):
    intensity_path = tmp_path / "grid_carbon_intensity.csv"
    _write_intensity_file(
        intensity_path,
        rows=[
            "VIC1,Victoria,2024-01-01 08:00:00,2024-01-01 09:00:00,0.40,Synthetic test fixture,,test,synthetic test row",
            "VIC1,Victoria,2024-01-01 08:15:00,2024-01-01 09:15:00,0.45,Synthetic test fixture,,test,synthetic test row",
        ],
    )

    with pytest.raises(ValueError, match="duplicate region/hour"):
        load_grid_carbon_intensity(intensity_path)


def test_build_time_varying_emissions_joins_hourly_factors(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    intensity_path = tmp_path / "grid_carbon_intensity.csv"
    _create_carbon_intensity_test_database(db_path)
    _write_intensity_file(
        intensity_path,
        rows=[
            "VIC1,Victoria,2024-01-01 08:00:00,2024-01-01 09:00:00,0.40,Synthetic test fixture,,test,synthetic test row",
        ],
    )

    table = build_time_varying_emissions(db_path, intensity_path)

    assert table.reference_row_count == 1
    assert table.gold_row_count == 2
    assert table.matched_hourly_factor_count == 1
    assert table.fallback_static_factor_count == 1
    assert table.missing_hourly_factor_count == 0

    with duckdb.connect(str(db_path)) as connection:
        rows = connection.execute(
            """
            SELECT
                usage_hour,
                static_estimated_emissions_kg_co2e,
                time_varying_estimated_emissions_kg_co2e,
                factor_match_status
            FROM gold.gold_hourly_time_varying_emissions
            ORDER BY usage_hour
            """
        ).fetchall()

    assert rows[0][1:] == (78.0, 40.0, "matched_hourly_factor")
    assert rows[1][1:] == (39.0, None, "fallback_static_factor")


def test_build_time_varying_emissions_handles_missing_reference_file(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    intensity_path = tmp_path / "missing_grid_carbon_intensity.csv"
    _create_carbon_intensity_test_database(db_path)

    table = build_time_varying_emissions(db_path, intensity_path)

    assert table.reference_row_count == 0
    assert table.gold_row_count == 2
    assert table.matched_hourly_factor_count == 0
    assert table.fallback_static_factor_count == 2
    assert table.missing_hourly_factor_count == 0


def test_write_carbon_intensity_report_creates_markdown(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    intensity_path = tmp_path / "grid_carbon_intensity.csv"
    report_path = tmp_path / "reports" / "time_varying_emissions_report.md"
    _create_carbon_intensity_test_database(db_path)
    _write_intensity_file(
        intensity_path,
        rows=[
            "VIC1,Victoria,2024-01-01 08:00:00,2024-01-01 09:00:00,0.40,Synthetic test fixture,,test,synthetic test row",
        ],
    )
    table = build_time_varying_emissions(db_path, intensity_path)

    write_carbon_intensity_report(table, db_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "Time-Varying Carbon Intensity Report" in report
    assert "not carbon accounting compliance" in report


def _create_carbon_intensity_test_database(db_path):
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
            (1, 'building_consumption', 10, NULL, '2024-01-01 09:00:00', 50.0, 1,
             '2024-01-01 09:00:00', '2024-01-01 09:00:00')
            """
        )
        connection.execute(
            """
            CREATE TABLE gold.gold_electricity_emissions (
                campus_id BIGINT,
                source_system VARCHAR,
                usage_month DATE,
                total_consumption DOUBLE,
                factor_id VARCHAR,
                factor_region VARCHAR,
                factor_year BIGINT,
                emissions_factor_kg_co2e_per_kwh DOUBLE,
                factor_source_name VARCHAR,
                factor_source_url VARCHAR,
                used_default_factor BOOLEAN,
                factor_notes VARCHAR,
                estimated_emissions_kg_co2e DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_electricity_emissions VALUES
            (1, 'building_consumption', '2024-01-01', 150.0, 'dcceew_nga_2025_vic_scope2',
             'Victoria', 2025, 0.78, 'DCCEEW National Greenhouse Accounts Factors 2025',
             'https://www.dcceew.gov.au/sites/default/files/documents/national-greenhouse-account-factors-2025.pdf',
             TRUE, 'Scope 2 only', 117.0)
            """
        )


def _write_intensity_file(path, rows):
    path.write_text(
        "\n".join(
            [
                "region_code,region_name,interval_start,interval_end,"
                "emissions_intensity_kg_co2e_per_kwh,source_name,source_url,data_version,notes",
                *rows,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
