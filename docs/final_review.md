# Final Review

## Purpose

This review checks that the Campus Utility Intelligence project is reproducible, documented, and aligned with the implemented resume claim.

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
```

## Results

- Tests passed: 24 tests
- Lint passed: no Ruff issues
- Profiling report generated: `reports/profile_report.md`
- Bronze ingestion loaded 11 raw CSV files
- Silver transformations created 3 cleaned electricity tables
- Quality checks passed: 18 passed, 0 failed
- Gold metrics created 4 tables
- Estimated emissions created 1 table
- SQL analytics generated 4 markdown query outputs
- NMI/building reconciliation created 2 tables

## Data Outcomes

Bronze ingestion loaded:

- `building_consumption.csv`: 8,095,524 rows
- `building_meta.csv`: 64 rows
- `building_submeter_consumption.csv`: 1,665,162 rows
- `calender.csv`: 2,312 rows
- `campus_meta.csv`: 5 rows
- `events.csv`: 106 rows
- `gas_consumption.csv`: 27,164 rows
- `nmi_consumption.csv`: 3,507,076 rows
- `nmi_meta.csv`: 14 rows
- `water_consumption.csv`: 245,040 rows
- `weather_data.csv`: 7,396,520 rows

Silver electricity tables contain:

- `silver.silver_building_electricity_readings`: 8,087,031 rows
- `silver.silver_nmi_electricity_readings`: 3,352,909 rows
- `silver.silver_submeter_electricity_readings`: 1,312,363 rows

Gold analytics tables contain:

- `gold.gold_hourly_electricity_usage`: 2,987,097 rows
- `gold.gold_daily_electricity_usage`: 18,974 rows
- `gold.gold_monthly_electricity_usage`: 633 rows
- `gold.gold_peak_demand`: 14 rows
- `gold.gold_electricity_emissions`: 633 rows
- `gold.gold_daily_nmi_building_reconciliation`: 12,925 rows
- `gold.gold_monthly_nmi_building_reconciliation`: 425 rows

## Implemented Features

- Project setup
- Kaggle dataset download
- Raw data profiling
- Bronze ingestion
- Silver electricity cleaning
- Data-quality checks
- Gold usage and peak-demand metrics
- Estimated emissions metrics
- SQL analytics queries
- NMI/building reconciliation
- Local Streamlit dashboard

## Resume Alignment

The project now supports this claim:

> Campus Utility Intelligence: Energy Usage Analytics Mart: Built a Python/SQL analytics mart using Kaggle UNICON campus utility data, aggregating high-frequency electricity readings into reporting-ready tables, implementing data-quality checks, peak-demand analysis, estimated emissions metrics, SQL analytics, and a local dashboard for facility-level energy efficiency insights.

## Known Limitations

- The dashboard is local only and not deployed.
- Emissions use a configurable estimate, not a verified official project-specific factor.
- NMI/building reconciliation quantifies gaps but cannot attribute them to exact physical causes such as street lighting or outdoor loads.
- Weather, water, and gas are profiled and ingested but not modeled into analytics marts.
- Forecasting and cloud deployment are not implemented.

## Git Review

Work was committed feature by feature. Raw data, generated reports, DuckDB files, caches, and virtual environments remain ignored by git.
