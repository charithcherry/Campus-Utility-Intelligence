# Feature 17: Demand-Response Event Simulator

## Goal

Add a simulator that evaluates whether campus flexible load could meet a grid-stress event reduction target.

## Status

Implemented.

## Files Changed

- `src/campus_utility/demand_response.py`
- `tests/test_demand_response.py`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/architecture.md`
- `docs/features/feature_17_demand_response_event_simulator.md`
- `README.md`
- `Makefile`

## Implementation Details

Implemented event inputs:

```text
event_date
start_hour
end_hour
target_reduction_percent
flexible_load_percent
rebound_window_hours
```

The current CLI implements event date, start/end hour, target reduction percent, flexible load percent, and rebound window. Target-kW mode, campus filtering, and meter filtering can be added later if dashboard or CLI workflows need them.

Output table:

```text
gold.gold_demand_response_simulation
```

Implemented metrics:

- Baseline event-window load
- Simulated event-window load
- Achieved reduction
- Unmet reduction
- Rebound load after the event
- Total energy preservation status
- Emissions impact placeholder, left empty unless real time-varying carbon intensity exists

## Source Context

Google Cloud has discussed demand response for data centers as a grid-support pattern:

```text
https://cloud.google.com/blog/products/infrastructure/using-demand-response-to-reduce-data-center-power-consumption
```

This project should treat demand response as an offline simulation only.

## How To Run It

Command:

```bash
make demand-response
```

## Tests Or Validation Performed

```bash
make test
make lint
make demand-response
```

Results:

- `43 passed`
- Ruff passed
- `gold.gold_demand_response_simulation`: 81 rows
- Events meeting target: 81
- Energy preservation failures: 0
- Negative load failures: 0
- Max achieved reduction: 1,746.7860

Automated tests cover:

- Event-window filtering
- Target reduction calculation
- Rebound accounting
- Energy preservation
- No negative simulated load
- Unmet target behavior
- Markdown report output

## Known Limitations

- Not a production optimizer.
- Not real-time grid control.
- Does not imply utility program participation.
- Estimated emissions impact should only be calculated when valid emissions factors exist for the event window.
- Current implementation is peak-only and does not optimize against carbon intensity.
- Default event parameters are a reproducible example, not a recommendation.

## Next Steps

Optional next step: add dashboard views for demand-response readiness or add campus/meter filters to the CLI.
