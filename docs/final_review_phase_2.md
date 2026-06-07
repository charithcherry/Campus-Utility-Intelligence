# Final Review Phase 2

## Purpose

This review verifies the completed Phase 2 project state. No new feature scope was added during this review; the work was limited to validation, documentation, and small correctness fixes found by the validation run.

## Commands Run

```bash
make test
make lint
make profile
make ingest
make transform
make quality
make metrics
make emissions
make analytics
make reconcile
make baseline
make simulate-shift
make dashboard
make test
make lint
```

## Test and Lint Results

- Initial test run: `32 passed`
- Initial lint run: `All checks passed!`
- Final test run after documentation, SQL polish, and peak-shift validation polish: `33 passed`
- Final lint run after documentation and SQL polish: `All checks passed!`

## Validation Findings

The first full validation run found that `sql/marts/monthly_emissions_summary.sql` still referenced the old emissions column `emissions_factor_kg_co2e_per_unit`. The current Phase 2 emissions table uses `emissions_factor_kg_co2e_per_kwh`.

The query was updated, then `make analytics`, `make reconcile`, `make baseline`, and `make simulate-shift` were rerun successfully.

The review also found that peak-shift energy preservation was being asserted by construction. The simulator now recomputes the simulated peak-hour, target-hour, and daily totals, then excludes scenarios where shifting would create a worse peak. A regression test was added for that case.

## Raw and Bronze Outcomes

Bronze ingestion loaded 11 raw Kaggle UNICON files into DuckDB:

| Table | Rows |
| --- | ---: |
| `bronze.bronze_building_consumption` | 8,095,524 |
| `bronze.bronze_building_meta` | 64 |
| `bronze.bronze_building_submeter_consumption` | 1,665,162 |
| `bronze.bronze_calender` | 2,312 |
| `bronze.bronze_campus_meta` | 5 |
| `bronze.bronze_events` | 106 |
| `bronze.bronze_gas_consumption` | 27,164 |
| `bronze.bronze_nmi_consumption` | 3,507,076 |
| `bronze.bronze_nmi_meta` | 14 |
| `bronze.bronze_water_consumption` | 245,040 |
| `bronze.bronze_weather_data` | 7,396,520 |

## Silver Outcomes

Silver cleaning produced reporting-ready electricity readings:

| Table | Rows |
| --- | ---: |
| `silver.silver_building_electricity_readings` | 8,087,031 |
| `silver.silver_nmi_electricity_readings` | 3,352,909 |
| `silver.silver_submeter_electricity_readings` | 1,312,363 |

Data-quality checks passed: `18 passed, 0 failed`.

## Gold Outcomes

Gold marts created by the project:

| Table | Rows |
| --- | ---: |
| `gold.gold_hourly_electricity_usage` | 2,987,097 |
| `gold.gold_daily_electricity_usage` | 18,974 |
| `gold.gold_monthly_electricity_usage` | 633 |
| `gold.gold_peak_demand` | 14 |
| `gold.gold_electricity_emissions` | 633 |
| `gold.gold_daily_nmi_building_reconciliation` | 12,925 |
| `gold.gold_monthly_nmi_building_reconciliation` | 425 |
| `gold.gold_weather_normalized_usage` | 2,642,240 |
| `gold.gold_peak_shift_simulation` | 55,759 |

Reference table:

| Table | Rows |
| --- | ---: |
| `reference.reference_emissions_factors` | 1 |

## Phase 2 Tables

Phase 2 added three decision-support outputs:

- `reference.reference_emissions_factors`
- `gold.gold_weather_normalized_usage`
- `gold.gold_peak_shift_simulation`

The confirmed DCCEEW NGA 2025 Victoria Scope 2 electricity factor is `0.78 kg CO2-e/kWh`.

The weather baseline output contains `393,608` high-usage investigation candidates.

The peak-shift scenarios contain:

- 5% flexible load: `19,059` rows
- 10% flexible load: `18,585` rows
- 15% flexible load: `18,115` rows

## Reports Generated

The validation flow generated or refreshed:

- `reports/profile_report.md`
- `reports/bronze_ingestion_report.md`
- `reports/silver_transform_report.md`
- `reports/data_quality_report.md`
- `reports/gold_metrics_report.md`
- `reports/emissions_metrics_report.md`
- `reports/sql_analytics_report.md`
- `reports/sql_analytics/`
- `reports/reconciliation_report.md`
- `reports/weather_baseline_report.md`
- `reports/peak_shift_report.md`

## Dashboard Verification

`make dashboard` launched successfully on `http://localhost:8501`, then the server was stopped.

Verified dashboard sections:

- Monthly usage
- Peak demand
- Emissions and emissions assumptions
- NMI/building reconciliation
- Weather-normalized baseline
- Peak-shifting simulation

The Phase 2 dashboard views expose emissions assumptions, weather-normalized high-usage investigation candidates, and offline peak-shift scenarios. The dashboard is local only and is not deployed.

## Commit History Summary

The project was built feature by feature:

- Project setup
- Kaggle dataset setup and profiling
- Bronze ingestion
- Silver electricity cleaning
- Data-quality checks
- Gold usage and peak-demand metrics
- Estimated emissions metrics
- SQL analytics queries
- NMI/building reconciliation
- Streamlit dashboard
- Phase 2 sustainability plan
- DCCEEW-based emissions factor reference data
- Weather-normalized baseline
- Peak-shifting simulation
- Phase 2 dashboard extensions
- Phase 2 final review

## Data Assumptions

- Raw data comes from the Kaggle UNICON campus utility dataset.
- NMI readings are campus-level utility meter readings, not building-level readings.
- Building, submeter, and NMI data are modeled separately and then reconciled where comparable.
- Weather data is used for baseline modeling where campus and timestamp matches are available.
- Water and gas are profiled and ingested, but the current decision-support marts focus on electricity.

## Emissions Limitations

- Emissions are estimated Scope 2 location-based electricity emissions only.
- The project uses the DCCEEW NGA 2025 Victoria Scope 2 factor: `0.78 kg CO2-e/kWh`.
- Scope 3 is documented in the source context but not used in calculations.
- The same 2025 factor is applied across historical electricity usage years, so outputs are decision-support estimates, not formal carbon accounting.
- This project does not provide carbon accounting compliance reporting.

## Weather Baseline Limitations

- `gold.gold_weather_normalized_usage` uses an explainable grouped-median baseline, not a causal model.
- Expected usage is based on similar campus, source, meter, optional building, hour, weekday, month, and temperature-band conditions.
- High-usage candidates are investigation candidates, not confirmed waste, faults, or guaranteed savings.
- Weather normalization can highlight unusual usage, but facilities context is still needed before action.

## Peak-Shift Simulation Limitations

- `gold.gold_peak_shift_simulation` is an offline simulation, not a production optimizer.
- It uses hourly electricity consumption as a peak-load proxy.
- Scenarios shift flexible load within the same day and preserve total daily kWh.
- Validation confirmed `0` energy preservation failures and `0` worse-peak scenarios in the final simulation output.
- Because emissions use a static DCCEEW Scope 2 factor, same-day shifting does not reduce estimated emissions when total kWh is preserved.
- No emissions reduction is claimed under the static emissions-factor assumption.

## Reproducibility Notes

Run the project locally with:

```bash
make install
make download-data
make profile
make ingest
make transform
make quality
make metrics
make emissions
make analytics
make reconcile
make baseline
make simulate-shift
make dashboard
```

Kaggle credentials are required for `make download-data`. If raw files are already present in `data/raw/`, the workflow can start at `make profile`.

## Git Hygiene Check

`git status --ignored --short` confirmed that raw data, processed DuckDB files, generated reports, caches, virtual environments, and package build metadata are ignored and not committed.

Ignored local outputs include:

- `.venv/`
- `.pytest_cache/`
- `.ruff_cache/`
- `data/raw/`
- `data/processed/`
- `reports/`
- `src/campus_utility_intelligence.egg-info/`
- Python `__pycache__/` directories

Planning scratch files `Implementation.md` and `optional_implementation.md` remain untracked and are not part of the committed project.

## Final Resume-Ready Project Claim

Campus Utility Intelligence: Built a Python/SQL sustainability analytics mart over Kaggle UNICON utility data with DuckDB gold tables, data-quality checks, peak-demand analysis, DCCEEW-based estimated Scope 2 emissions, weather-normalized efficiency scoring, peak-shifting simulations, SQL analytics, NMI/building reconciliation, and a Streamlit dashboard.
