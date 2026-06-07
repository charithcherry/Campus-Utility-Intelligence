# Feature 5: Data-Quality Checks

## Goal

Validate cleaned silver electricity tables before building metrics or dashboard-ready marts.

## Files Changed

- `Makefile`
- `README.md`
- `src/campus_utility/quality.py`
- `tests/test_quality.py`
- `docs/validation_rules.md`
- `docs/features/feature_5_data_quality_checks.md`

## Implementation Details

The quality workflow checks that silver tables have rows, required fields are not null, consumption is non-negative, meter/timestamp keys are unique, timestamp coverage exists, and campus IDs map to campus metadata.

The command writes `reports/data_quality_report.md` and exits with an error if any required check fails.

## How To Run It

```bash
make quality
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make quality
```

## Known Limitations

These checks validate silver electricity tables only. Gold marts, emissions metrics, and dashboard checks are not implemented yet.

## Next Steps

Implement Feature 6: Peak-demand and usage metrics.
