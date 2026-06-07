# Feature 15: Dashboard Visualization Polish

## Goal

Plan a dashboard polish feature that makes the Streamlit app feel like an energy intelligence product without adding new backend pipeline tables.

The dashboard story should be:

```text
What happened? -> Why did it happen? -> Is it abnormal? -> What can we do? -> Can we trust the data?
```

## Status

Planned. This feature is not implemented yet.

## Expected Files To Change

- `dashboard/app.py`
- `src/campus_utility/dashboard_data.py`
- `tests/test_dashboard_data.py`
- `README.md`
- `docs/features/feature_15_dashboard_visualization_polish.md`

Optional if screenshots are added:

- `docs/assets/`
- `README.md`

## Expected Dashboard Structure

Use sidebar navigation with these pages:

- Executive Overview
- Usage Patterns
- Emissions
- Weather-Normalized Efficiency
- Peak-Shifting Simulator
- NMI/Building Reconciliation
- Data Quality
- Methodology and Assumptions

## Executive Overview

Add first-page KPI cards:

- Total electricity usage in kWh or MWh
- Estimated Scope 2 emissions in tCO2e
- Peak demand
- High-usage candidate rate
- Best simulated peak reduction

Each card should include a small delta versus the previous month or previous comparable period where the data supports it.

Add summary charts:

- Monthly electricity usage trend with campus filter
- Estimated Scope 2 emissions trend using the DCCEEW factor
- Best peak-shift scenario comparison for 5%, 10%, and 15% flexible load

## Usage Patterns

Add charts that explain how electricity usage behaves over time:

- Monthly usage by campus as a stacked or grouped bar chart
- Hour-of-day and day-of-week heatmap
- Daily usage calendar-style heatmap if practical in Streamlit
- Top 10 or top 20 meters/buildings by usage

Avoid too many raw time-series lines because they become hard to read.

## Weather-Normalized Efficiency

Add charts based on `gold.gold_weather_normalized_usage`:

- Actual versus expected usage line chart
- Residual usage chart where residual means `actual - expected`
- Efficiency opportunity ranking
- High-usage candidate rate over time
- Temperature versus usage scatter plot

Use the label `high-usage candidate`, not waste, fault, or savings.

## Peak-Shifting Simulator

Add charts based on `gold.gold_peak_shift_simulation`:

- Scenario comparison for 5%, 10%, and 15% flexible load
- Before versus after peak chart for a representative high-peak day, if the available table fields support it
- Peak reduction leaderboard
- Energy preservation check card

The energy preservation card should show:

- Energy preservation failures
- Negative simulated peaks
- Worse peaks

The page must include this assumption:

```text
Because emissions use a static DCCEEW Scope 2 factor, same-day shifting preserves total estimated emissions when total kWh is preserved. This simulation focuses on peak-demand reduction, not emissions reduction.
```

## Data Quality And Trust

Add a page that explains why the data can be trusted:

- Medallion pipeline row-count funnel from bronze to silver to gold
- Quality checks status table
- Dropped or filtered records summary where reports expose this information
- NMI versus building reconciliation gap chart

## Chart Design Rules

- Prefer Plotly or Altair for important charts.
- Use clear titles and axis units.
- Add short insight captions under charts.
- Use compact numbers such as `2.4M kWh`.
- Keep filters above charts.
- Sort bars.
- Limit leaderboards to top 10 or top 20.
- Avoid pie charts.
- Avoid huge unreadable legends.
- Use consistent units: kWh, MWh, tCO2e, and peak kW where applicable.

## Accuracy Rules

- Do not add new backend claims unless new backend logic is implemented.
- Do not claim emissions reduction from same-day shifting while the project uses a static DCCEEW Scope 2 factor.
- Do not label high-usage candidates as confirmed waste, faults, or savings.
- Do not claim production optimization or real-time control.
- Do not claim dashboard deployment unless it is deployed.

## Acceptance Criteria

- Multi-page dashboard navigation exists.
- Executive KPI cards exist.
- Hour-of-day and day-of-week heatmap exists.
- Actual versus expected usage chart exists.
- Efficiency opportunity ranking exists.
- Peak-shift scenario comparison exists.
- Data quality and trust page exists.
- Pages include concise assumptions and insight captions.
- Dashboard remains robust when optional Phase 2 tables are missing.
- Tests pass.

## Tests Or Validation

Run:

```bash
make test
make lint
make dashboard
```

Manual validation:

- Confirm dashboard starts locally.
- Confirm each page loads.
- Confirm charts have units and filters.
- Confirm no page claims emissions reduction from peak shifting.
- Stop the Streamlit server after validation.

## Known Limitations

This planned feature improves presentation and decision-support storytelling. It should not change pipeline semantics unless a separate backend feature is approved.

## Next Steps

Implement this only after approval. This is a dashboard polish feature, not a new data-modeling feature.
