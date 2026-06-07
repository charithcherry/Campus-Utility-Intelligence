# Feature 7: Estimated Emissions Metrics

## Goal

Create estimated electricity emissions metrics from gold monthly usage.

## Files Changed

- `.env.example`
- `Makefile`
- `README.md`
- `src/campus_utility/config.py`
- `src/campus_utility/emissions.py`
- `tests/test_config.py`
- `tests/test_emissions.py`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/features/feature_7_estimated_emissions_metrics.md`

## Implementation Details

The emissions workflow creates `gold.gold_electricity_emissions` from `gold.gold_monthly_electricity_usage`.

It multiplies `total_consumption` by a configurable emissions factor and stores both the factor and estimated emissions on each row.

## How To Run It

```bash
make emissions
```

The emissions report is written to:

```text
reports/emissions_metrics_report.md
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make emissions
```

## Known Limitations

The default emissions factor is a configurable estimate, not a verified official project-specific factor. Replace it when a specific factor is required.

## Next Steps

Implement SQL analytics queries or dashboard views.
