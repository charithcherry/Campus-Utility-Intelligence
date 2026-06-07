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
2. Feature 17: Demand-Response Event Simulator: implemented
3. Feature 18: Demand-Response Dashboard and Scenario Polish: implemented
4. Feature 19: Documentation-Aware Analytics Copilot: implemented
5. Feature 20: Gemini Tool-Calling Analytics Agent: implemented
6. Stop for review before considering forecasting or anomaly workbench

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

Status: implemented.

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

## Feature 18: Demand-Response Dashboard And Scenario Polish

Status: implemented.

Goal: make demand-response simulation visible in the Streamlit dashboard and clarify the scenario assumptions behind the results.

Implemented behavior:

- Added a `Grid Event Readiness` dashboard page.
- Shows simulated events, events meeting target, target achievement rate, achieved reduction, unmet reduction, rebound load, energy preservation failures, and negative load failures.
- Adds a load comparison chart for baseline event load, simulated event load, and rebound load.
- Updates the report with default target, flexible-load, and rebound assumptions.
- Clearly labels the output as offline simulation, not real operational proof.

Command:

```bash
make dashboard
```

Suggested commit:

```text
feat: add demand-response dashboard views
```

## Feature 19: Documentation-Aware Analytics Copilot

Status: implemented.

Goal: answer project documentation and metric questions using docs retrieval plus safe read-only DuckDB SQL.

Implemented behavior:

- Indexes README, docs, feature notes, final reviews, and local generated markdown reports when present.
- Does not embed raw meter rows.
- Routes supported metric questions to safe read-only SQL.
- Blocks unsafe SQL.
- Adds an `Analytics Copilot` dashboard page.
- Uses local fallback behavior when Gemini is not configured.

Command:

```bash
make copilot-check
```

Suggested commit:

```text
feat: add documentation-aware analytics copilot
```

## Feature 20: Gemini Tool-Calling Analytics Agent

Status: implemented.

Goal: upgrade the analytics copilot into a Gemini agent that can choose project-document retrieval, table inspection, project snapshot, and safe read-only SQL tools before answering.

Implemented behavior:

- Every Gemini-enabled question goes through the Gemini tool-calling loop.
- Available tools are `retrieve_project_docs`, `list_tables`, `describe_table`, `run_read_only_sql`, and `get_project_snapshot`.
- The dashboard shows Gemini mode status, final answer, tool calls made, SQL used, result preview, retrieved sources, and safety notes.
- If `GEMINI_API_KEY` is missing or Gemini fails, the copilot falls back to local retrieval and predefined metric SQL routes.
- SQL remains read-only and blocks mutating statements.

Command:

```bash
make copilot-check
```

Suggested commit:

```text
feat: upgrade copilot to Gemini tool-calling agent
```

## Feature 21: Forecasting And Peak-Risk Alerts

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

## Feature 21: Energy Anomaly Investigation

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

## Target Resume Claim After Features 16 And 17

If Features 16 and 17 are implemented truthfully, the project could support:

> Campus Utility Intelligence: Built a grid-aware sustainability analytics platform over Kaggle UNICON utility data with DuckDB gold marts, DCCEEW-based Scope 2 estimates, time-varying carbon-intensity modeling, weather-normalized efficiency scoring, peak-shifting simulation, demand-response readiness analysis, NMI/building reconciliation, and a Streamlit dashboard.
