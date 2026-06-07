# Campus Utility Intelligence

Campus Utility Intelligence is a local Python, SQL, DuckDB, and Streamlit analytics project for campus electricity usage data.

Current status: project setup, Kaggle download, raw profiling, bronze ingestion, silver electricity cleaning, data-quality checks, gold electricity metrics, estimated emissions metrics, SQL analytics queries, NMI/building reconciliation, weather-normalized baseline, and a local Streamlit dashboard are implemented.

## What Is Implemented

- Python package scaffold under `src/campus_utility/`
- Local configuration defaults for raw data and DuckDB output paths
- Makefile commands for installation, tests, linting, and future workflow entry points
- Placeholder Streamlit dashboard entry point
- Documentation structure for architecture, data dictionary, validation rules, decision log, and feature notes
- Git ignore rules for raw data, generated data, reports, caches, virtual environments, and local secrets
- Raw data profiling workflow that writes `reports/profile_report.md`
- Kaggle download command for the UNICON dataset
- Bronze ingestion workflow that loads raw files into DuckDB
- Silver electricity cleaning workflow for building, NMI, and submeter readings
- Data-quality checks for cleaned silver electricity tables
- Gold usage and peak-demand metric tables
- Estimated electricity emissions metric table
- Reusable SQL analytics queries with markdown outputs
- Campus-level NMI versus building usage reconciliation
- Weather-normalized electricity baseline and high-usage candidate scoring
- Local Streamlit dashboard for usage, peak demand, emissions, and reconciliation

## Project Layout

```text
data/
  raw/
  interim/
  processed/
docs/
  features/
sql/
  bronze/
  silver/
  gold/
  marts/
src/
  campus_utility/
dashboard/
tests/
```

## Setup

Install the project into a local virtual environment:

```bash
make install
```

Run tests:

```bash
make test
```

Profile raw data:

```bash
make profile
```

Ingest raw data into DuckDB bronze tables:

```bash
make ingest
```

This creates `data/processed/campus_utility.duckdb` and `reports/bronze_ingestion_report.md`.

Create cleaned silver electricity tables:

```bash
make transform
```

This creates silver tables in the same DuckDB database and writes `reports/silver_transform_report.md`.

Run data-quality checks:

```bash
make quality
```

This validates silver tables and writes `reports/data_quality_report.md`.

Build usage and peak-demand metrics:

```bash
make metrics
```

This creates gold tables and writes `reports/gold_metrics_report.md`.

Build estimated emissions metrics:

```bash
make emissions
```

This creates `gold.gold_electricity_emissions` and writes `reports/emissions_metrics_report.md`.

By default, emissions factors are loaded from `data/reference/emissions_factors_example.csv`. Override this with:

```bash
CAMPUS_EMISSIONS_FACTORS_PATH=/path/to/factors.csv make emissions
```

The included reference factor is the DCCEEW 2025 National Greenhouse Accounts Factors Victoria location-based purchased electricity Scope 2 factor: `0.78 kg CO2-e/kWh`. It excludes the related Scope 3 factor.

Run SQL analytics queries:

```bash
make analytics
```

This writes query outputs to `reports/sql_analytics/` and an index at `reports/sql_analytics_report.md`.

Reconcile NMI and building usage:

```bash
make reconcile
```

This creates reconciliation tables and writes `reports/reconciliation_report.md`.

Build weather-normalized baseline:

```bash
make baseline
```

This creates `gold.gold_weather_normalized_usage` and writes `reports/weather_baseline_report.md`.

Download the UNICON dataset from Kaggle:

```bash
make download-data
```

This requires Kaggle API credentials at `~/.kaggle/kaggle.json`.

Run the placeholder dashboard:

```bash
make dashboard
```

## Data Handling

Raw Kaggle files should be placed under `data/raw/`. Raw data and generated outputs are ignored by git.

The profiling workflow currently supports `.csv`, `.json`, `.jsonl`, and `.parquet` files.

## Known Limitations

Estimated emissions use configurable reference factors. The included factor is an official DCCEEW Victoria Scope 2 electricity factor, but it should still be reviewed before formal reporting. The dashboard is local only and is not deployed.

## Final Review

See `docs/final_review.md` for the end-to-end validation summary, data outcomes, known limitations, and resume alignment.

## Phase 2 Plan

See `docs/phase_2_plan.md` for the next sustainability intelligence features:

- Australia-aware emissions factor reference data
- Weather-normalized energy baseline
- Carbon-aware peak-shifting simulator
- Dashboard extensions
