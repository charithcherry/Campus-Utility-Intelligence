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

## Automated Quality Report

Feature 5 adds `make quality`, which writes `reports/data_quality_report.md`.

The report checks:

- Row counts are positive
- Required fields are not null
- Consumption is non-negative
- Meter/timestamp keys are unique
- Timestamp min and max values exist
- Campus IDs map to `bronze.bronze_campus_meta`

The command exits with an error if any required check fails.

## Gold Metrics Validation

Feature 6 validates gold metrics with unit tests that check hourly aggregation and NMI peak-demand selection.

Gold tables should be regenerated after `make transform` and `make quality`.
