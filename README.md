# Campus Utility Intelligence

Campus Utility Intelligence is a local Python, SQL, DuckDB, and Streamlit analytics project for campus electricity usage data.

Current status: project setup, Kaggle download, raw profiling, bronze ingestion, silver electricity cleaning, data-quality checks, gold electricity metrics, estimated emissions metrics, SQL analytics queries, and NMI/building reconciliation are implemented. Dashboard views are planned future features.

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

This repository does not yet create dashboard views. Estimated emissions use a configurable factor and should be replaced if an official project-specific factor is required.
