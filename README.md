# Campus Utility Intelligence

Campus Utility Intelligence is a local Python, SQL, DuckDB, and Streamlit analytics project for campus electricity usage data.

Current status: project setup is implemented. Data profiling, ingestion, transformations, analytics marts, quality checks, and dashboard views are planned future features.

## What Is Implemented

- Python package scaffold under `src/campus_utility/`
- Local configuration defaults for raw data and DuckDB output paths
- Makefile commands for installation, tests, linting, and future workflow entry points
- Placeholder Streamlit dashboard entry point
- Documentation structure for architecture, data dictionary, validation rules, decision log, and feature notes
- Git ignore rules for raw data, generated data, reports, caches, virtual environments, and local secrets
- Raw data profiling workflow that writes `reports/profile_report.md`
- Kaggle download command for the UNICON dataset

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

This repository does not yet ingest or transform the Kaggle UNICON dataset. Profiling is implemented, but no actual raw data has been profiled in this workspace yet.
