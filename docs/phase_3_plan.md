# Phase 3 Plan: Grid-Aware Decision Support

## Purpose

Phase 3 is planned future work. It should add one high-impact grid-aware layer at a time instead of adding many unrelated features.

The goal is to move the project from:

```text
sustainability analytics dashboard
```

to:

```text
grid-aware decision-support system
```

The target story is:

```text
What happened? -> Is it abnormal? -> What can we do? -> When should flexible load run?
```

## Current Baseline

The project already has:

- Static DCCEEW Scope 2 emissions estimates
- Weather-normalized high-usage candidate scoring
- Offline same-day peak-shifting simulation
- Streamlit dashboard views for usage, emissions, weather efficiency, peak shifting, reconciliation, and data quality

Current limitation: emissions use a static factor. Same-day peak shifting does not reduce estimated emissions when total kWh is preserved.

## Recommended Order

1. Feature 16: Time-Varying Carbon Intensity Layer: implemented
2. Feature 17: Demand-Response Event Simulator: planned
3. Stop for review before considering forecasting, anomaly workbench, or RAG

## Feature 16: Time-Varying Carbon Intensity Layer

Status: implemented.

Goal: add optional hourly grid carbon-intensity data so the project can compare static Scope 2 emissions with time-varying grid-aware emissions estimates.

Why it matters:

- The current DCCEEW factor is credible but static.
- Time-varying intensity makes emissions-aware load shifting possible without overclaiming.
- This lets the simulator compare peak-only shifting against lower-carbon shift windows.

Expected behavior:

- Add optional ingestion for grid carbon intensity, ideally Victoria/NEM region.
- Create a reference table such as `reference.reference_grid_carbon_intensity_hourly`.
- Join hourly electricity usage to hourly grid emissions intensity.
- Calculate hourly estimated emissions.
- Compare static DCCEEW estimates against time-varying estimates.
- Update peak-shift simulation to support strategies:
  - lowest demand hour
  - lowest carbon hour
  - balanced demand and carbon score

Candidate sources:

- Open Electricity emissions data and documentation: `https://docs.openelectricity.org.au/guides/emissions/`
- Electricity Maps carbon-intensity APIs may be evaluated if access and licensing fit the project.

Accuracy rules:

- Do not invent intensity values.
- Do not ship demo values as official values.
- Clearly separate static Scope 2 estimates from time-varying operational grid-intensity estimates.
- Document source, region, timestamp grain, unit, and license/access assumptions.

Command:

```bash
make carbon-intensity
```

Suggested commit:

```text
feat: add time-varying carbon intensity layer
```

## Feature 17: Demand-Response Event Simulator

Status: planned.

Goal: simulate whether campus flexible load could meet a grid-event reduction target.

Why it matters:

- It moves the project from analytics into operational grid-flexibility planning.
- It aligns with demand-response patterns where large infrastructure operators reduce or shift load during grid stress.

Expected behavior:

- Let the user define a grid event:
  - event date
  - start hour
  - end hour
  - target reduction percent or target kW
  - campuses/meters included
- Simulate flexible-load reduction during the event window.
- Track achieved reduction, unmet reduction, rebound load, total energy preservation, and estimated emissions impact.
- Add a dashboard page named `Grid Event Readiness`.

Candidate source context:

- Google Cloud demand-response discussion: `https://cloud.google.com/blog/products/infrastructure/using-demand-response-to-reduce-data-center-power-consumption`

Accuracy rules:

- Treat this as simulation, not production control.
- Do not claim real-time operations.
- Do not claim utility program participation.
- Preserve energy accounting unless a scenario explicitly models curtailment.

Suggested command:

```bash
make demand-response
```

Suggested commit:

```text
feat: add demand-response event simulator
```

## Feature 18: Forecasting And Peak-Risk Alerts

Status: planned.

Goal: forecast future hourly electricity usage and identify peak-risk windows before they happen.

Expected behavior:

- Start with a simple baseline such as seasonal naive or lag-feature regression.
- Forecast next-day or next-week hourly electricity usage.
- Output predicted peak demand, high-risk peak hours, forecast uncertainty, and recommended shift windows.
- Compare forecast accuracy against a simple baseline before adding heavier models.

Candidate source context:

- Building-energy forecasting research, including time-series foundation model work, can be reviewed later.

Accuracy rules:

- Do not claim production forecasting until backtesting is implemented.
- Do not add complex models unless they beat simple baselines.
- Always report forecast error.

Suggested command:

```bash
make forecast
```

Suggested commit:

```text
feat: add peak-risk forecasting baseline
```

## Feature 19: Energy Anomaly Investigation

Status: planned.

Goal: turn weather-normalized residuals into an investigation workflow.

Expected behavior:

- Rank anomalies by residual severity.
- Group anomalies by campus, building, meter, hour, weekday/weekend, and source.
- Add explanation labels such as:
  - weather-driven
  - overnight load
  - weekend load
  - sudden spike
  - missing data
  - reconciliation gap
- Add dashboard drilldown for top anomaly candidates.

Accuracy rules:

- Keep using `candidate` language.
- Do not claim confirmed faults without external validation.
- Treat explanations as heuristic labels, not root-cause proof.

Suggested command:

```bash
make anomalies
```

Suggested commit:

```text
feat: add anomaly investigation workflow
```

## Optional Later Feature: RAG And SQL Copilot

Status: optional future work after Feature 16 or Feature 17.

Goal: answer project questions using docs, reports, and read-only DuckDB SQL.

Expected behavior:

- Build retrieval over README, docs, data dictionary, validation reports, and final reviews.
- Add read-only SQL access to DuckDB for metric questions.
- Do not embed raw electricity rows.
- Cite docs and SQL outputs in answers.
- Validate generated SQL before execution.

Good questions:

- How are emissions calculated?
- Which campus had the highest peak demand?
- Why does same-day shifting not reduce emissions under a static factor?
- Show top high-usage candidates.
- What assumptions are used in the weather baseline?

## Target Resume Claim After Features 16 And 17

If Features 16 and 17 are implemented truthfully, the project could support:

> Campus Utility Intelligence: Built a grid-aware sustainability analytics platform over Kaggle UNICON utility data with DuckDB gold marts, DCCEEW-based Scope 2 estimates, time-varying carbon-intensity modeling, weather-normalized efficiency scoring, peak-shifting simulation, demand-response readiness analysis, NMI/building reconciliation, and a Streamlit dashboard.
