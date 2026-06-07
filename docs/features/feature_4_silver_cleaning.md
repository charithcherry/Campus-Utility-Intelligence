# Feature 4: Silver Cleaning and Normalization

## Goal

Create cleaned silver electricity tables from bronze data.

## Files Changed

- `Makefile`
- `README.md`
- `src/campus_utility/transformations.py`
- `tests/test_transformations.py`
- `docs/architecture.md`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/validation_rules.md`
- `docs/features/feature_4_silver_cleaning.md`

## Implementation Details

The silver workflow creates three electricity tables:

- `silver.silver_building_electricity_readings`
- `silver.silver_nmi_electricity_readings`
- `silver.silver_submeter_electricity_readings`

Silver filters rows with missing required IDs, timestamps, or consumption values. It also removes negative consumption values and deduplicates repeated meter/timestamp records.

## How To Run It

```bash
make transform
```

The transform report is written to:

```text
reports/silver_transform_report.md
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make transform
```

## Known Limitations

Final unit definitions are still not assumed. Silver keeps source-specific readings separate instead of forcing one combined table.

Metadata enrichment is not implemented yet.

## Next Steps

Implement Feature 5: Data-Quality Checks.
