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

## Silver Validation

Feature 4 validates silver cleaning with:

- Required ID, timestamp, and consumption fields are not null
- Consumption is non-negative
- Repeated meter/timestamp records are deduplicated
- NMI campus IDs parse to integers
- Transform reports include row counts for each silver table

Silver validation is focused on electricity tables only.
