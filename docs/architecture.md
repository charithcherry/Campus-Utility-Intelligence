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
