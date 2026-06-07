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

The emissions workflow now loads factors from `data/reference/emissions_factors_example.csv` by default. The current reference file uses the DCCEEW 2025 National Greenhouse Accounts Factors Victoria location-based purchased electricity Scope 2 factor of `0.78 kg CO2-e/kWh`.

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

The included factor is official DCCEEW reference data, but emissions are still estimates and should not be treated as carbon accounting compliance results. The current file uses Scope 2 only, excludes the related Victoria Scope 3 factor of `0.09 kg CO2-e/kWh`, and applies the 2025 factor as the project default across historical usage years.

## Recommended Factor Sources

The preferred source for static Australia emissions factors is Australia's National Greenhouse Accounts Factors from the Department of Climate Change, Energy, the Environment and Water. DCCEEW states that the NGA Factors provide emissions factors and methods to help estimate greenhouse gas emissions and are revised yearly.

For more advanced time-varying grid emissions intensity, future work can evaluate sources such as Open Electricity or CSIRO. Open Electricity documents emissions as energy generated multiplied by an emissions intensity factor and provides Australian grid emissions data. CSIRO has datasets for consumption-based emissions intensity estimates for National Electricity Market regions.

The project should not invent official values. Users should provide or update the factor CSV when they want a different region, year, scope, or source-specific factor.

## Next Steps

Implement Feature 12: Weather-normalized energy baseline and efficiency opportunity scoring.
