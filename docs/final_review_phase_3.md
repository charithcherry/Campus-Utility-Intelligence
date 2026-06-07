# Final Review Phase 3

## Purpose

This review verifies the completed project after Phase 3 additions. No new feature scope was added during this review; the work was limited to validation, documentation, and README accuracy.

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
make carbon-intensity
make demand-response
make dashboard
make test
make lint
```

## Final Test And Lint Results

- Initial test run: `43 passed`
- Initial lint run: `All checks passed!`
- Final test run after documentation: `43 passed`
- Final lint run after documentation: `All checks passed!`

## Tables Created Or Verified

Bronze tables:

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

Silver tables:

| Table | Rows |
| --- | ---: |
| `silver.silver_building_electricity_readings` | 8,087,031 |
| `silver.silver_nmi_electricity_readings` | 3,352,909 |
| `silver.silver_submeter_electricity_readings` | 1,312,363 |

Gold and reference tables:

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
| `gold.gold_peak_shift_simulation` | 55,748 |
| `gold.gold_hourly_time_varying_emissions` | 2,987,097 |
| `gold.gold_demand_response_simulation` | 81 |
| `reference.reference_emissions_factors` | 1 |
| `reference.reference_grid_carbon_intensity_hourly` | 0 |

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
- `reports/time_varying_emissions_report.md`
- `reports/demand_response_report.md`

## Dashboard Pages Verified

`make dashboard` launched successfully on `http://localhost:8501`, then the server was stopped.

Verified dashboard pages:

- Executive Overview
- Usage Patterns
- Emissions
- Weather-Normalized Efficiency
- Peak-Shifting Simulator
- Grid Event Readiness
- NMI/Building Reconciliation
- Data Quality
- Methodology and Assumptions

## Phase 1 Summary

Phase 1 built the local analytics foundation:

- Project setup
- Kaggle UNICON download workflow
- Raw profiling
- Bronze ingestion into DuckDB
- Silver electricity cleaning
- Data-quality checks
- Gold usage and peak-demand tables
- Static estimated emissions
- SQL analytics outputs
- NMI/building reconciliation
- Initial local Streamlit dashboard

## Phase 2 Summary

Phase 2 added decision-support analytics:

- DCCEEW NGA 2025 Victoria Scope 2 factor: `0.78 kg CO2-e/kWh`
- Weather-normalized usage baseline
- High-usage investigation candidates
- Peak-shifting simulation
- Dashboard extensions and visualization polish

Phase 2 kept the core accuracy rule: same-day shifting does not claim emissions reduction while emissions use a static Scope 2 factor.

## Phase 3 Summary

Phase 3 added grid-aware simulation support:

- Optional time-varying carbon-intensity ingestion support
- Static DCCEEW fallback when no real hourly carbon-intensity file is loaded
- Hourly time-varying emissions comparison table
- Demand-response event simulation
- Grid Event Readiness dashboard page

Confirmed Phase 3 results:

- `reference.reference_grid_carbon_intensity_hourly`: `0` rows because no real hourly file is loaded
- `gold.gold_hourly_time_varying_emissions`: `2,987,097` rows
- Carbon match status: `2,987,097` rows use `fallback_static_factor`
- `gold.gold_demand_response_simulation`: `81` rows
- Demand-response events meeting target: `81`
- Demand-response energy preservation failures: `0`
- Demand-response negative load failures: `0`

Because every hourly emissions row uses `fallback_static_factor`, the project supports optional time-varying carbon-intensity ingestion but does not yet claim emissions-aware optimization.

## Data Assumptions

- Raw utility data comes from the Kaggle UNICON dataset.
- NMI readings are campus-level utility meter readings, not building-level readings.
- Building, submeter, and NMI data are modeled separately because they have different grains.
- Water, gas, and weather are ingested and profiled, but the main gold decision-support marts focus on electricity.
- Raw data and generated DuckDB/report outputs are local artifacts and are not committed.

## Emissions Assumptions

- Static emissions are estimated Scope 2 location-based electricity emissions.
- The project uses the DCCEEW NGA 2025 Victoria Scope 2 factor: `0.78 kg CO2-e/kWh`.
- Scope 3 is documented but not used.
- The same 2025 factor is applied across historical usage years, so outputs are decision-support estimates, not formal carbon accounting.
- This project does not provide carbon accounting compliance reporting.

## Weather Baseline Limitations

- `gold.gold_weather_normalized_usage` uses an explainable grouped-median baseline, not a causal model.
- High-usage records are investigation candidates, not confirmed waste, faults, or savings.
- Confirmed output: `393,608` high-usage investigation candidates out of `2,642,240` baseline rows.

## Peak-Shifting Limitations

- `gold.gold_peak_shift_simulation` is an offline simulation, not a production optimizer.
- It uses hourly electricity consumption as a peak-load proxy.
- Scenarios preserve same-day total kWh.
- Confirmed output: `55,748` rows, `0` energy preservation failures, `0` negative simulated peaks, and `0` worse peaks.
- No emissions reduction is claimed under the static DCCEEW factor.

## Time-Varying Carbon-Intensity Limitation

- `make carbon-intensity` supports user-provided hourly grid carbon-intensity data.
- No real hourly carbon-intensity file is loaded locally.
- `reference.reference_grid_carbon_intensity_hourly` has `0` rows.
- All `2,987,097` hourly emissions rows use `fallback_static_factor`.
- Therefore, the project does not yet claim official hourly carbon-intensity modeling or emissions-aware shifting.

## Demand-Response Simulation Limitations

- `gold.gold_demand_response_simulation` is an offline event simulation.
- It is not real-time grid control.
- It does not imply utility demand-response program participation.
- It is not proof of real operational flexibility.
- The `81/81` target achievement result comes from a feasible default scenario: `10%` target reduction, `15%` flexible-load assumption, and `3` hour rebound window.
- Emissions impact is not calculated unless real time-varying carbon intensity is loaded.

## Git Hygiene Check

`git status --ignored --short` confirmed that local artifacts remain uncommitted:

- Raw Kaggle data: ignored under `data/raw/`
- DuckDB processed database files: ignored under `data/processed/`
- Generated reports: ignored under `reports/`
- Virtual environment: ignored under `.venv/`
- Caches: ignored under `.pytest_cache/`, `.ruff_cache/`, and `__pycache__/`
- Local package metadata: ignored under `src/campus_utility_intelligence.egg-info/`

No `.env`, Kaggle credentials, raw large data, DuckDB files, reports, caches, or virtual environments are committed.

Planning scratch files `Implementation.md` and `optional_implementation.md` remain untracked and are not part of the committed project.

## Final Resume-Ready Project Line

Campus Utility Intelligence: Built a Python/SQL sustainability analytics mart over Kaggle UNICON utility data with DuckDB gold tables, data-quality checks, peak-demand analysis, DCCEEW-based Scope 2 emissions, weather-normalized efficiency scoring, peak-shifting simulations, optional time-varying carbon-intensity support, demand-response event simulation, SQL analytics, NMI/building reconciliation, and a multi-page Streamlit dashboard.
