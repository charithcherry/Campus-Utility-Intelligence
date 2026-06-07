# Feature 18: Demand-Response Dashboard And Scenario Polish

## Goal

Make demand-response simulation results visible and explainable in the Streamlit dashboard, and improve the report so feasible default results are not overinterpreted.

## Status

Implemented.

## Files Changed

- `dashboard/app.py`
- `src/campus_utility/dashboard_data.py`
- `src/campus_utility/demand_response.py`
- `tests/test_dashboard_data.py`
- `docs/features/feature_18_demand_response_dashboard_polish.md`
- `docs/features/feature_19_forecasting_peak_risk_alerts.md`
- `docs/features/feature_20_energy_anomaly_investigation.md`
- `docs/phase_3_plan.md`
- `README.md`

## Implementation Details

The dashboard now includes a `Grid Event Readiness` page that reads from:

```text
gold.gold_demand_response_simulation
```

The page shows:

- Total simulated events
- Events meeting target
- Target achievement rate
- Achieved reduction
- Unmet reduction
- Rebound load
- Energy preservation failures
- Negative load failures
- Baseline event load versus simulated event load versus rebound load
- Scenario settings and top simulated reductions

The demand-response report now includes:

- Event date
- Event window
- Target reduction assumption
- Flexible-load assumption
- Rebound-window assumption
- Accuracy note explaining that 100% target achievement means the configured target was feasible under the assumptions, not proof of real operational flexibility

## How To Run It

```bash
make demand-response
make dashboard
```

## Tests Or Validation Performed

```bash
make test
make lint
make demand-response
make dashboard
```

Results:

- `43 passed`
- Ruff passed
- `gold.gold_demand_response_simulation`: 81 rows
- Events meeting target: 81
- Energy preservation failures: 0
- Negative load failures: 0
- Dashboard launched successfully

## Known Limitations

- This is still an offline simulation.
- It does not prove real operational flexibility.
- It does not imply utility demand-response program participation.
- It does not calculate emissions impact unless real time-varying carbon intensity exists.
- Scenario sensitivity is limited to the current configured output; no invented low/medium/aggressive scenario rows were added.

## Next Steps

Proceed to Final Review Phase 3 and stop building unless a new feature is explicitly approved.
