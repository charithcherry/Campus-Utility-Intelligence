# Feature 16: Time-Varying Carbon Intensity Layer

## Goal

Plan an optional hourly grid carbon-intensity layer so the project can compare static DCCEEW Scope 2 estimates with time-varying grid-aware emissions estimates.

## Status

Planned. This feature is not implemented yet.

## Files Expected To Change

- `src/campus_utility/carbon_intensity.py`
- `src/campus_utility/peak_shift.py`
- `src/campus_utility/dashboard_data.py`
- `dashboard/app.py`
- `tests/test_carbon_intensity.py`
- `tests/test_peak_shift.py`
- `data/reference/`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/features/feature_16_time_varying_carbon_intensity.md`
- `README.md`
- `Makefile`

## Implementation Details

Expected output table:

```text
reference.reference_grid_carbon_intensity_hourly
```

Expected fields:

```text
region
network
intensity_timestamp
emissions_intensity_kg_co2e_per_kwh
source_name
source_url
source_version
unit
notes
```

Expected gold output:

```text
gold.gold_hourly_time_varying_emissions
```

Expected behavior:

- Load verified hourly carbon-intensity data from a source file or API export.
- Join hourly electricity usage to hourly carbon intensity by timestamp and region.
- Calculate hourly time-varying estimated emissions.
- Compare static DCCEEW emissions with time-varying estimates.
- Extend peak-shift simulation with carbon-aware strategies only after real intensity data exists.

## Source Candidates

- Open Electricity emissions documentation: `https://docs.openelectricity.org.au/guides/emissions/`
- Electricity Maps may be evaluated for past/latest/forecast carbon-intensity data if API access and licensing fit the project.

## How To Run It

Planned command:

```bash
make carbon-intensity
```

## Tests Or Validation To Perform

- Schema check for reference intensity table
- Source metadata check
- Timestamp coverage check
- Null intensity check
- Unit conversion test
- Join coverage test between hourly usage and intensity
- Static versus time-varying comparison test
- Peak-shift strategy test for lowest-demand, lowest-carbon, and balanced strategies

## Known Limitations

- Do not invent carbon-intensity values.
- Do not claim compliance reporting.
- Time-varying operational intensity is not the same as official Scope 2 accounting.
- Source licensing and API access must be checked before committing any reference data.

## Next Steps

Implement only after approving Feature 16 and selecting a valid data source.
