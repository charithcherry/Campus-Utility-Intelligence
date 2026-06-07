import duckdb

from campus_utility.dashboard_data import (
    get_filter_options,
    load_emissions,
    load_emissions_assumptions,
    load_executive_summary,
    load_hourly_usage_heatmap,
    load_monthly_usage,
    load_monthly_usage_by_campus,
    load_peak_demand,
    load_peak_shift_scenario_comparison,
    load_peak_shift_summary,
    load_pipeline_row_counts,
    load_quality_check_summary,
    load_top_peak_shift_results,
    load_temperature_usage_sample,
    load_top_usage_entities,
    load_top_weather_baseline_candidates,
    load_weather_actual_expected_trend,
    load_weather_baseline_summary,
    load_weather_candidate_rate_trend,
    load_reconciliation,
    table_exists,
)


def test_dashboard_data_helpers_load_expected_frames(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    _create_dashboard_test_database(db_path)

    campuses, sources = get_filter_options(db_path)
    usage = load_monthly_usage(db_path, campuses, sources)
    executive_summary = load_executive_summary(db_path, campuses, sources)
    usage_by_campus = load_monthly_usage_by_campus(db_path, campuses, sources)
    hourly_heatmap = load_hourly_usage_heatmap(db_path, campuses, sources)
    top_usage = load_top_usage_entities(db_path, campuses, sources)
    emissions = load_emissions(db_path, campuses, sources)
    assumptions = load_emissions_assumptions(db_path)
    peak = load_peak_demand(db_path, campuses)
    reconciliation = load_reconciliation(db_path, campuses)
    baseline_summary = load_weather_baseline_summary(db_path, campuses)
    actual_expected = load_weather_actual_expected_trend(db_path, campuses, sources)
    candidate_rate = load_weather_candidate_rate_trend(db_path, campuses, sources)
    temp_sample = load_temperature_usage_sample(db_path, campuses, sources)
    baseline_candidates = load_top_weather_baseline_candidates(db_path, campuses)
    shift_comparison = load_peak_shift_scenario_comparison(db_path, campuses, sources)
    shift_summary = load_peak_shift_summary(db_path, campuses, 0.10)
    shift_results = load_top_peak_shift_results(db_path, campuses, 0.10)
    row_counts = load_pipeline_row_counts(db_path)
    quality_summary = load_quality_check_summary(db_path)

    assert campuses == [1]
    assert sources == ["building_consumption"]
    assert table_exists(db_path, "gold", "gold_weather_normalized_usage")
    assert usage["total_consumption"].sum() == 100.0
    assert executive_summary["total_consumption"] == 100.0
    assert executive_summary["best_peak_reduction"] == 10.0
    assert usage_by_campus["total_consumption"].sum() == 100.0
    assert hourly_heatmap["avg_consumption"].iloc[0] == 100.0
    assert top_usage["total_consumption"].iloc[0] == 100.0
    assert emissions["estimated_emissions_kg_co2e"].sum() == 78.0
    assert assumptions["emissions_factor_kg_co2e_per_kwh"].iloc[0] == 0.78
    assert peak["peak_demand_kw"].iloc[0] == 90.0
    assert reconciliation["consumption_difference"].iloc[0] == 20.0
    assert baseline_summary["high_usage_candidates"].iloc[0] == 1
    assert actual_expected["residual_consumption"].iloc[0] == 50.0
    assert candidate_rate["high_usage_rate"].iloc[0] == 1.0
    assert temp_sample["air_temperature"].iloc[0] == 30.0
    assert baseline_candidates["efficiency_opportunity_score"].iloc[0] == 50.0
    assert shift_comparison["valid_scenarios"].iloc[0] == 1
    assert shift_summary["avg_peak_reduction"].iloc[0] == 10.0
    assert shift_results["total_energy_preserved"].iloc[0]
    assert row_counts["row_count"].sum() > 0
    assert quality_summary.empty


def _create_dashboard_test_database(db_path):
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
            (1, 'building_consumption', '2024-01-01', 100.0, 'dcceew_nga_2025_vic_scope2',
             'Victoria', 2025, 0.78, 'DCCEEW National Greenhouse Accounts Factors 2025',
             'https://www.dcceew.gov.au/sites/default/files/documents/national-greenhouse-account-factors-2025.pdf',
             TRUE, 'Scope 2 only', 78.0)
            """
        )
        connection.execute(
            """
            CREATE TABLE gold.gold_peak_demand (
                campus_id BIGINT,
                meter_id BIGINT,
                peak_timestamp TIMESTAMP,
                peak_demand_kw DOUBLE,
                peak_demand_kva DOUBLE,
                consumption_at_peak DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_peak_demand VALUES
            (1, 20, '2024-01-01 00:00:00', 90.0, 95.0, 35.0)
            """
        )
        connection.execute(
            """
            CREATE TABLE gold.gold_monthly_nmi_building_reconciliation (
                campus_id BIGINT,
                usage_month DATE,
                nmi_consumption DOUBLE,
                building_consumption DOUBLE,
                consumption_difference DOUBLE,
                difference_ratio_to_nmi DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_monthly_nmi_building_reconciliation VALUES
            (1, '2024-01-01', 100.0, 80.0, 20.0, 0.2)
            """
        )
        connection.execute(
            """
            CREATE TABLE gold.gold_weather_normalized_usage (
                campus_id BIGINT,
                source_system VARCHAR,
                meter_id BIGINT,
                building_id BIGINT,
                usage_hour TIMESTAMP,
                actual_consumption DOUBLE,
                expected_consumption DOUBLE,
                residual_consumption DOUBLE,
                residual_percent DOUBLE,
                air_temperature DOUBLE,
                is_high_usage_candidate BOOLEAN,
                efficiency_opportunity_score DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_weather_normalized_usage VALUES
            (1, 'building_consumption', 10, NULL, '2024-01-01 08:00:00',
             150.0, 100.0, 50.0, 0.5, 30.0, TRUE, 50.0)
            """
        )
        connection.execute(
            """
            CREATE TABLE gold.gold_hourly_electricity_usage (
                campus_id BIGINT,
                source_system VARCHAR,
                meter_id BIGINT,
                building_id BIGINT,
                usage_hour TIMESTAMP,
                total_consumption DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_hourly_electricity_usage VALUES
            (1, 'building_consumption', 10, NULL, '2024-01-01 08:00:00', 100.0)
            """
        )
        connection.execute(
            """
            CREATE TABLE gold.gold_peak_shift_simulation (
                campus_id BIGINT,
                source_system VARCHAR,
                meter_id BIGINT,
                building_id BIGINT,
                simulation_date DATE,
                flexible_load_percent DOUBLE,
                baseline_peak_consumption DOUBLE,
                simulated_peak_consumption DOUBLE,
                peak_reduction DOUBLE,
                peak_reduction_percent DOUBLE,
                total_energy_preserved BOOLEAN,
                negative_usage_created BOOLEAN,
                notes VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO gold.gold_peak_shift_simulation VALUES
            (1, 'building_consumption', 10, NULL, '2024-01-01', 0.10,
             100.0, 90.0, 10.0, 0.10, TRUE, FALSE, 'Static factor emissions unchanged')
            """
        )
