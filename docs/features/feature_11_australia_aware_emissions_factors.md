# Feature 11: Australia-Aware Emissions Factor Support

## Goal

Load configurable emissions factor reference data and store factor metadata in the gold emissions output.

## Files Changed

- `.env.example`
- `.gitignore`
- `README.md`
- `data/reference/emissions_factors_example.csv`
- `src/campus_utility/config.py`
- `src/campus_utility/emissions.py`
- `tests/test_config.py`
- `tests/test_emissions.py`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/validation_rules.md`
- `docs/features/feature_11_australia_aware_emissions_factors.md`

## Implementation Details

The emissions workflow now loads factors from `data/reference/emissions_factors_example.csv` by default. The workflow creates `reference.reference_emissions_factors` and joins monthly electricity usage to the best available factor.

Selection prefers source-specific factors over wildcard factors and exact-year factors over older factors. If no source-specific factor exists, the workflow uses a documented default factor where available.

The gold emissions table now includes factor ID, country, region, energy type, factor year, source name, source URL, default flag, notes, factor value, and estimated emissions.

## How To Run It

```bash
make emissions
```

Override the factor file:

```bash
CAMPUS_EMISSIONS_FACTORS_PATH=/path/to/factors.csv make emissions
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make emissions
```

## Known Limitations

The included factor is a demo estimate, not an official project-specific emissions factor. Emissions are estimates and should not be treated as carbon accounting compliance results.

## Next Steps

Implement Feature 12: Weather-normalized energy baseline and efficiency opportunity scoring.
