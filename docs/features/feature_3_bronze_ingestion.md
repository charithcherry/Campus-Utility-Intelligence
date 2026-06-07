# Feature 3: Bronze Ingestion

## Goal

Load raw Kaggle UNICON files from `data/raw/` into DuckDB bronze tables with minimal transformation.

## Files Changed

- `Makefile`
- `README.md`
- `src/campus_utility/database.py`
- `src/campus_utility/ingestion.py`
- `tests/test_ingestion.py`
- `docs/architecture.md`
- `docs/features/feature_3_bronze_ingestion.md`

## Implementation Details

The ingestion workflow discovers supported raw files and loads each CSV into the DuckDB `bronze` schema.

Bronze table names use the source filename with a `bronze_` prefix. For example, `building_consumption.csv` becomes `bronze.bronze_building_consumption`.

The workflow drops and recreates each bronze table on every run so ingestion is repeatable.

## How To Run It

```bash
make ingest
```

The DuckDB database is written to:

```text
data/processed/campus_utility.duckdb
```

The ingestion report is written to:

```text
reports/bronze_ingestion_report.md
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make ingest
```

Validation includes unit tests with a synthetic CSV and a real ingestion run against the downloaded Kaggle files.

The real run loaded 11 bronze tables and reconciled row counts with the profiling report.

## Known Limitations

Bronze ingestion currently uses DuckDB CSV type inference and does not enforce final schemas.

Raw timestamps, units, duplicates, and invalid readings are not cleaned in bronze. Those rules belong in the silver layer.

## Next Steps

Implement Feature 4: Silver Cleaning and Normalization.
