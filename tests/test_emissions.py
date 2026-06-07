import duckdb
import pytest

from campus_utility.emissions import (
    build_emissions_metrics,
    load_emissions_factors,
    write_emissions_report,
)


def test_load_emissions_factors_validates_required_columns(tmp_path):
    factors_path = tmp_path / "bad_factors.csv"
    factors_path.write_text("factor_id,country\nbad,Australia\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        load_emissions_factors(factors_path)


def test_build_emissions_metrics_prefers_source_specific_factor(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    factors_path = tmp_path / "emissions_factors.csv"
    _create_emissions_test_database(db_path)
    _write_factor_file(
        factors_path,
        rows=[
            "default_au,Australia,Australia,*,electricity,2024,0.50,Demo estimate,,true,Default demo factor",
            "building_au,Australia,Australia,building_consumption,electricity,2024,0.25,Building estimate,,false,Source-specific demo factor",
        ],
    )

    table = build_emissions_metrics(db_path, factors_path)

    assert table.table_name == "gold.gold_electricity_emissions"
    assert table.row_count == 1
    assert table.factor_count == 2
    assert table.default_factor_count == 0

    with duckdb.connect(str(db_path)) as connection:
        rows = connection.execute(
            """
            SELECT total_consumption, factor_id, emissions_factor_kg_co2e_per_kwh,
                   used_default_factor, estimated_emissions_kg_co2e
            FROM gold.gold_electricity_emissions
            """
        ).fetchall()

    assert rows == [(100.0, "building_au", 0.25, False, 25.0)]


def test_build_emissions_metrics_falls_back_to_default_factor(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    factors_path = tmp_path / "emissions_factors.csv"
    _create_emissions_test_database(db_path)
    _write_factor_file(
        factors_path,
        rows=[
            "default_au,Australia,Australia,*,electricity,2024,0.50,Demo estimate,,true,Default demo factor",
        ],
    )

    table = build_emissions_metrics(db_path, factors_path)

    assert table.default_factor_count == 1

    with duckdb.connect(str(db_path)) as connection:
        rows = connection.execute(
            """
            SELECT factor_id, emissions_factor_kg_co2e_per_kwh, used_default_factor,
                   estimated_emissions_kg_co2e
            FROM gold.gold_electricity_emissions
            """
        ).fetchall()

    assert rows == [("default_au", 0.5, True, 50.0)]


def test_build_emissions_metrics_allows_default_factor_across_years(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    factors_path = tmp_path / "emissions_factors.csv"
    _create_emissions_test_database(db_path)
    _write_factor_file(
        factors_path,
        rows=[
            "default_future,Australia,Australia,*,electricity,2026,0.50,Demo estimate,,true,Default demo factor",
        ],
    )

    table = build_emissions_metrics(db_path, factors_path)

    assert table.row_count == 1
    assert table.default_factor_count == 1


def test_write_emissions_report_creates_markdown(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    factors_path = tmp_path / "emissions_factors.csv"
    report_path = tmp_path / "reports" / "emissions_metrics_report.md"
    _create_emissions_test_database(db_path)
    _write_factor_file(
        factors_path,
        rows=[
            "default_au,Australia,Australia,*,electricity,2024,0.50,Demo estimate,,true,Default demo factor",
        ],
    )
    table = build_emissions_metrics(db_path, factors_path)

    write_emissions_report(table, db_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert "Emissions Metrics Report" in report
    assert "reference.reference_emissions_factors" in report


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


def _write_factor_file(path, rows):
    path.write_text(
        "\n".join(
            [
                "factor_id,country,region,source_system,energy_type,factor_year,"
                "emissions_factor_kg_co2e_per_kwh,factor_source_name,factor_source_url,"
                "is_default,notes",
                *rows,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
