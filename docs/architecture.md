# Architecture

Campus Utility Intelligence will use a local medallion-style analytics architecture:

1. Raw Kaggle files in `data/raw/`
2. Bronze DuckDB tables with minimal transformation
3. Silver cleaned electricity readings
4. Gold reporting marts for usage, peak demand, and emissions estimates
5. SQL analytics and Streamlit dashboard views

Feature 1 establishes the repository structure only. Data ingestion and transformations are planned future features.

## Bronze Layer

Feature 3 loads raw files into `data/processed/campus_utility.duckdb` under the DuckDB `bronze` schema.

Bronze tables preserve source columns with minimal transformation. Cleaning, standardization, and business rules are deferred to silver and gold layers.

## Silver Layer

Feature 4 creates cleaned electricity tables in the DuckDB `silver` schema.

The silver layer standardizes required ID fields, timestamps, and numeric reading columns. It filters missing required values, removes negative consumption rows, and deduplicates repeated meter/timestamp records.

## Gold Layer

Feature 6 creates reporting-ready electricity metrics in the DuckDB `gold` schema.

Gold tables aggregate silver readings into hourly, daily, and monthly usage. Peak-demand metrics use NMI demand readings to identify the highest observed demand per campus and meter.

## SQL Analytics

Feature 8 stores reusable SQL report queries under `sql/marts/`.

The analytics runner executes those queries against DuckDB and writes markdown outputs under `reports/sql_analytics/`.

## Reconciliation

Feature 9 compares campus-level NMI electricity totals against summed campus-level building meter totals.

This is a diagnostic layer for source alignment. It does not assume NMI and building readings should always match.

## Dashboard

Feature 10 adds a local Streamlit dashboard over DuckDB gold tables.

The dashboard uses the existing gold outputs for usage trends, peak demand, estimated emissions, and NMI/building reconciliation.

## Weather-Normalized Baseline

Feature 12 joins hourly electricity usage to campus weather and creates `gold.gold_weather_normalized_usage`.

The model is an explainable grouped median baseline by campus, source, meter, optional building, hour, day of week, month, and temperature band.

## Peak-Shifting Simulation

Feature 13 creates `gold.gold_peak_shift_simulation`.

The simulator shifts configurable flexible load from peak hourly consumption to lower same-day hourly consumption within each campus/source/meter/building group. It preserves total daily energy and does not claim emissions reduction under the current static emissions factor.

## Time-Varying Carbon Intensity

Feature 16 adds an optional reference layer for hourly grid carbon intensity.

The workflow reads a user-provided CSV from `CAMPUS_GRID_CARBON_INTENSITY_PATH`, creates `reference.reference_grid_carbon_intensity_hourly`, and joins it to `gold.gold_hourly_electricity_usage` to create `gold.gold_hourly_time_varying_emissions`.

If no hourly carbon-intensity file is present, the reference table is empty and the gold table uses deterministic static-factor fallback from `gold.gold_electricity_emissions`. This keeps the DCCEEW static emissions workflow as the default while allowing source-dependent operational grid-intensity analysis when valid data exists.

## Demand-Response Event Simulation

Feature 17 creates `gold.gold_demand_response_simulation`.

The simulator models an offline grid-stress event window. It estimates target reduction, achieved reduction, unmet reduction, rebound load after the event, and energy preservation using existing hourly electricity usage.

This is not real-time grid control and does not imply participation in a utility demand-response program. Emissions impact remains unset unless valid time-varying carbon-intensity data is loaded.
