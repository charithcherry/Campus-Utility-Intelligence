# Campus Utility Intelligence

Campus Utility Intelligence is a local Python, SQL, DuckDB, and Streamlit analytics project for campus electricity usage data.

Current status: project setup, Kaggle download, raw profiling, bronze ingestion, silver electricity cleaning, data-quality checks, gold electricity metrics, estimated emissions metrics, optional time-varying emissions comparison, SQL analytics queries, NMI/building reconciliation, weather-normalized baseline, peak-shifting simulation, demand-response event simulation, documentation-aware analytics copilot, and a local Streamlit dashboard are implemented.

## What Is Implemented

- Python package scaffold under `src/campus_utility/`
- Local configuration defaults for raw data and DuckDB output paths
- Makefile commands for installation, tests, linting, data pipelines, analytics, simulation, and dashboard launch
- Local Streamlit dashboard entry point
- Documentation structure for architecture, data dictionary, validation rules, decision log, and feature notes
- Git ignore rules for raw data, generated data, reports, caches, virtual environments, and local secrets
- Raw data profiling workflow that writes `reports/profile_report.md`
- Kaggle download command for the UNICON dataset
- Bronze ingestion workflow that loads raw files into DuckDB
- Silver electricity cleaning workflow for building, NMI, and submeter readings
- Data-quality checks for cleaned silver electricity tables
- Gold usage and peak-demand metric tables
- Estimated electricity emissions metric table
- Optional hourly time-varying emissions comparison with static-factor fallback
- Reusable SQL analytics queries with markdown outputs
- Campus-level NMI versus building usage reconciliation
- Weather-normalized electricity baseline and high-usage candidate scoring
- Offline demand-response event simulation for grid-stress target reduction and rebound analysis
- Documentation-aware analytics copilot with local retrieval, optional Gemini summaries, and safe read-only DuckDB metric queries
- Multi-page local Streamlit dashboard for executive KPIs, usage patterns, emissions, weather-normalized efficiency, peak-shift simulation, demand-response readiness, analytics copilot, reconciliation, data quality, and methodology notes

## Project Layout

```text
data/
  raw/
  interim/
  processed/
docs/
  features/
sql/
  bronze/
  silver/
  gold/
  marts/
src/
  campus_utility/
dashboard/
tests/
```

## Setup

Install the project into a local virtual environment:

```bash
make install
```

Run tests:

```bash
make test
```

Profile raw data:

```bash
make profile
```

Ingest raw data into DuckDB bronze tables:

```bash
make ingest
```

This creates `data/processed/campus_utility.duckdb` and `reports/bronze_ingestion_report.md`.

Create cleaned silver electricity tables:

```bash
make transform
```

This creates silver tables in the same DuckDB database and writes `reports/silver_transform_report.md`.

Run data-quality checks:

```bash
make quality
```

This validates silver tables and writes `reports/data_quality_report.md`.

Build usage and peak-demand metrics:

```bash
make metrics
```

This creates gold tables and writes `reports/gold_metrics_report.md`.

Build estimated emissions metrics:

```bash
make emissions
```

This creates `gold.gold_electricity_emissions` and writes `reports/emissions_metrics_report.md`.

By default, emissions factors are loaded from `data/reference/emissions_factors_example.csv`. Override this with:

```bash
CAMPUS_EMISSIONS_FACTORS_PATH=/path/to/factors.csv make emissions
```

The included reference factor is the DCCEEW 2025 National Greenhouse Accounts Factors Victoria location-based purchased electricity Scope 2 factor: `0.78 kg CO2-e/kWh`. It excludes the related Scope 3 factor.

Run SQL analytics queries:

```bash
make analytics
```

This writes query outputs to `reports/sql_analytics/` and an index at `reports/sql_analytics_report.md`.

Reconcile NMI and building usage:

```bash
make reconcile
```

This creates reconciliation tables and writes `reports/reconciliation_report.md`.

Build weather-normalized baseline:

```bash
make baseline
```

This creates `gold.gold_weather_normalized_usage` and writes `reports/weather_baseline_report.md`.

Run peak-shifting simulation:

```bash
make simulate-shift
```

This creates `gold.gold_peak_shift_simulation` and writes `reports/peak_shift_report.md`.

Run demand-response event simulation:

```bash
make demand-response
```

This creates `gold.gold_demand_response_simulation` and writes `reports/demand_response_report.md`. The default simulation is offline and peak-only; it does not claim real-time control or utility program participation.

Build optional time-varying emissions comparison:

```bash
make carbon-intensity
```

This creates `reference.reference_grid_carbon_intensity_hourly`, `gold.gold_hourly_time_varying_emissions`, and `reports/time_varying_emissions_report.md`.

By default, the command looks for:

```bash
data/reference/grid_carbon_intensity_hourly.csv
```

If no file is present, the reference table is empty and hourly rows fall back to the static DCCEEW factor. A tiny synthetic template is available at `data/reference/grid_carbon_intensity_example.csv`; it is not official data and should not be used for analysis.

Open the local dashboard:

```bash
make dashboard
```

The dashboard includes executive KPIs, usage patterns, emissions assumptions, NMI/building reconciliation, weather-normalized high-usage candidates, peak-shifting simulation views, demand-response readiness, analytics copilot, data-quality context, and methodology notes.

Run the analytics copilot smoke check:

```bash
make copilot-check
```

The copilot answers documentation questions from project docs and metric questions through safe read-only DuckDB SQL. It does not embed raw meter rows. If `GEMINI_API_KEY` is configured, it uses `GEMINI_MODEL`, defaulting to `gemini-3.5-flash`, to summarize retrieved snippets or SQL result previews. API keys belong in local environment variables only and must not be committed.

Download the UNICON dataset from Kaggle:

```bash
make download-data
```

This requires Kaggle API credentials at `~/.kaggle/kaggle.json`.

## Data Handling

Raw Kaggle files should be placed under `data/raw/`. Raw data and generated outputs are ignored by git.

The profiling workflow currently supports `.csv`, `.json`, `.jsonl`, and `.parquet` files.

## Known Limitations

Estimated emissions use configurable reference factors. The included factor is an official DCCEEW Victoria Scope 2 electricity factor, but it should still be reviewed before formal reporting. Time-varying emissions require user-provided hourly carbon-intensity data and are source-dependent. Demand-response output is an offline simulation, not real-time grid control. The copilot is lightweight and not production-ready. The dashboard is local only and is not deployed.

## Final Review

See `docs/final_review.md` for the first end-to-end validation summary. See `docs/final_review_phase_2.md` for the completed Phase 2 validation summary. See `docs/final_review_phase_3.md` for the final Phase 3 validation summary, grid-aware simulation outputs, limitations, and resume alignment.

## Future Work

See `docs/phase_3_plan.md` for grid-aware decision-support notes.

Optional later features are forecasting or anomaly investigation.
