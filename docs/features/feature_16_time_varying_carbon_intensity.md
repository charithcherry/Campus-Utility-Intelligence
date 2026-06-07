# Feature 16: Time-Varying Carbon Intensity Layer

## Goal

Add an optional hourly grid carbon-intensity layer so the project can compare static DCCEEW Scope 2 estimates with time-varying grid-aware emissions estimates.

## Status

Implemented.

## Files Changed

- `src/campus_utility/carbon_intensity.py`
- `tests/test_carbon_intensity.py`
- `src/campus_utility/config.py`
- `.env.example`
- `.gitignore`
- `Makefile`
- `data/reference/`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/architecture.md`
- `docs/features/feature_16_time_varying_carbon_intensity.md`
- `README.md`

## Implementation Details

Output reference table:

```text
reference.reference_grid_carbon_intensity_hourly
```

Reference fields:

```text
region
region_name
interval_start
interval_end
interval_start_hour
emissions_intensity_kg_co2e_per_kwh
source_name
source_url
data_version
is_synthetic
ingested_at
notes
```

Gold output:

```text
gold.gold_hourly_time_varying_emissions
```

Implemented behavior:

- Load hourly carbon-intensity data from a user-provided CSV when present.
- Join hourly electricity usage to hourly carbon intensity by timestamp and region.
- Calculate hourly time-varying estimated emissions.
- Compare static DCCEEW emissions with time-varying estimates.
- Fall back to static DCCEEW factors when hourly factors are missing.
- Keep peak-shift carbon-aware strategies for a later feature after real hourly intensity data is available.

## Source Candidates

- Open Electricity emissions documentation: `https://docs.openelectricity.org.au/guides/emissions/`
- Electricity Maps may be evaluated for past/latest/forecast carbon-intensity data if API access and licensing fit the project.

## How To Run It

Command:

```bash
make carbon-intensity
```

## Tests Or Validation Performed

```bash
make test
make lint
make carbon-intensity
```

Results:

- `39 passed`
- Ruff passed
- `reference.reference_grid_carbon_intensity_hourly`: 0 rows because no real hourly file exists locally
- `gold.gold_hourly_time_varying_emissions`: 2,987,097 rows
- `matched_hourly_factor`: 0 rows
- `fallback_static_factor`: 2,987,097 rows
- `missing_hourly_factor`: 0 rows

Automated tests cover:

- valid synthetic sample loading
- missing required columns
- negative intensity rejection
- duplicate region/hour rejection
- hourly factor join behavior
- missing-file static fallback behavior
- emissions calculation correctness

## Known Limitations

- Do not invent carbon-intensity values.
- Do not claim compliance reporting.
- Time-varying operational intensity is not the same as official Scope 2 accounting.
- Source licensing and API access must be checked before committing any reference data.
- The committed example CSV is synthetic and is not used as official data.
- Peak-shift carbon-aware optimization is not implemented in this feature.

## Next Steps

Feature 17 is the planned next feature: demand-response event simulator.
