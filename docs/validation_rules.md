# Validation Rules

Validation rules will be implemented after the silver electricity schema is defined.

Planned validation areas include schema checks, duplicate checks, timestamp coverage, missing values, invalid readings, and row-count reconciliation.

## Bronze Validation

Feature 3 validates bronze ingestion with:

- Table presence for each raw CSV file
- Row-count reconciliation against the profiling report
- Column-count reconciliation against the profiling report
- Idempotent table recreation on repeated `make ingest` runs

Bronze does not remove duplicates, clean timestamps, infer final units, or fix invalid readings.
