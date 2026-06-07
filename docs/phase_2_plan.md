# Phase 2 Plan: Sustainability Intelligence

## Purpose

Phase 2 extends the current analytics mart with sustainability-focused decision support. The goal is to add more intelligence on top of the existing bronze, silver, and gold pipeline without rewriting the project.

## Current Baseline

Version 1 already includes:

- Kaggle UNICON dataset setup and profiling
- Bronze ingestion into DuckDB
- Silver electricity cleaning and normalization
- Data-quality checks
- Gold usage and peak-demand metrics
- Estimated emissions metrics
- SQL analytics queries
- NMI/building reconciliation
- Local Streamlit dashboard
- Feature docs, tests, linting, and feature-by-feature commits

## Working Rules For Phase 2

Work feature by feature. Before each feature, state:

- Feature name
- Goal
- Files expected to change
- Acceptance criteria
- Tests or validation to run

After each feature:

- Update `README.md`
- Update or create a feature doc under `docs/features/`
- Update relevant docs such as `docs/data_dictionary.md`, `docs/architecture.md`, `docs/validation_rules.md`, and `docs/decision_log.md`
- Add or update tests
- Run relevant commands
- Commit only that feature
- Stop and wait for approval before moving to the next feature

## Accuracy Rules

- Do not fabricate official emissions factors, sources, external datasets, or performance results.
- If an official emissions factor is not included in the repository, use a configurable reference-table workflow and clearly mark defaults as demo estimates.
- Do not claim carbon accounting compliance.
- Do not claim production readiness.
- Do not claim real-time optimization.
- Describe peak shifting as an offline analytical simulation.

## Feature 11: Australia-Aware Emissions Factor Support

Goal: improve the emissions workflow so it loads factor metadata from configurable reference data instead of relying only on a single default factor.

Expected behavior:

- Add a reference emissions factor table.
- Support region, source, energy type, year, factor source, and notes.
- Join monthly electricity usage to the best available factor.
- Store factor metadata in the gold emissions output.
- Fall back deterministically to a clearly labeled default estimate.
- Document that emissions are estimates, not official carbon accounting results.

Recommended static factor source: Australia's National Greenhouse Accounts Factors from the Department of Climate Change, Energy, the Environment and Water. Feature 11 uses the DCCEEW 2025 Victoria Scope 2 electricity factor. More advanced time-varying grid emissions intensity can be evaluated later with sources such as Open Electricity or CSIRO, but values should not be invented.

Suggested command remains:

```bash
make emissions
```

Suggested commit:

```text
feat: add configurable emissions factor reference data
```

Stop after this feature and wait for approval.

## Feature 12: Weather-Normalized Energy Baseline

Goal: use ingested weather data to create an explainable baseline and identify high-usage candidates.

Expected behavior:

- Inspect real weather columns before joining.
- Build a simple explainable baseline.
- Create a table such as `gold.gold_weather_normalized_usage`.
- Include actual usage, expected usage, residuals, residual percent, model version, and opportunity score.
- Avoid claiming confirmed waste or faults.

Suggested command:

```bash
make baseline
```

Suggested commit:

```text
feat: add weather-normalized usage baseline
```

## Feature 13: Peak-Shifting Simulator

Goal: add an offline simulation that estimates peak-demand impact from shifting configurable flexible load.

Expected behavior:

- Use gold hourly electricity usage.
- Shift load within the same day.
- Preserve total daily energy.
- Avoid negative usage.
- Estimate before/after peak demand.
- Do not claim emissions reduction under the current static emissions factor.

Suggested command:

```bash
make simulate-shift
```

Suggested commit:

```text
feat: add peak-shifting simulation workflow
```

## Feature 14: Dashboard Extensions

Goal: extend the Streamlit dashboard with phase 2 outputs.

Expected dashboard additions:

- Emissions factor source and assumptions
- Weather-normalized actual vs expected usage
- Efficiency opportunity score
- Peak-shifting simulation before/after results
- Peak reduction summary
- Estimated emissions context, without reduction claims under the static factor

Suggested commit:

```text
feat: extend dashboard with efficiency and simulation views
```

## Feature 15: Dashboard Visualization Polish

Goal: improve the Streamlit dashboard presentation so it reads like an energy intelligence product without adding new backend pipeline tables.

Status: implemented after Phase 2 final review.

Expected behavior:

- Add sidebar navigation.
- Add an executive overview page.
- Add usage-pattern charts.
- Add weather-normalized efficiency charts.
- Add peak-shift scenario comparison charts.
- Add data quality and trust views.
- Add concise insight captions and assumption notes.
- Keep the static-emissions-factor limitation clear.
- Avoid claiming emissions reduction from same-day peak shifting.

Suggested command:

```bash
make dashboard
```

Suggested commit:

```text
feat: polish dashboard visualizations
```

## Phase 2 Final Review

After Features 11 to 14, run:

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
```

Then create:

```text
docs/final_review_phase_2.md
```

The review should include commands run, test results, new tables, new reports, dashboard sections, data assumptions, emissions limitations, simulation limitations, and updated resume alignment.

## Target Resume Claim After Phase 2

If all phase 2 features are implemented truthfully, the project should support:

> Campus Utility Intelligence: Built a Python/SQL sustainability analytics mart over Kaggle UNICON utility data with DuckDB gold tables, data-quality checks, peak-demand analysis, configurable emissions-factor modeling, weather-normalized efficiency scoring, peak-shifting simulations, SQL analytics, NMI/building reconciliation, and a Streamlit dashboard.
