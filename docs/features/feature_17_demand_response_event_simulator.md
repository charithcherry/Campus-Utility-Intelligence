# Feature 17: Demand-Response Event Simulator

## Goal

Plan a simulator that evaluates whether campus flexible load could meet a grid-stress event reduction target.

## Status

Planned. This feature is not implemented yet.

## Files Expected To Change

- `src/campus_utility/demand_response.py`
- `src/campus_utility/dashboard_data.py`
- `dashboard/app.py`
- `tests/test_demand_response.py`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/features/feature_17_demand_response_event_simulator.md`
- `README.md`
- `Makefile`

## Implementation Details

Expected event inputs:

```text
event_date
start_hour
end_hour
target_reduction_percent
target_reduction_kw
campus_ids
meter_ids
flexible_load_percent
rebound_window_hours
```

Expected output table:

```text
gold.gold_demand_response_simulation
```

Expected metrics:

- Baseline event-window load
- Simulated event-window load
- Achieved reduction
- Unmet reduction
- Rebound load after the event
- Total energy preservation status
- Estimated emissions impact, if time-varying carbon intensity exists

## Source Context

Google Cloud has discussed demand response for data centers as a grid-support pattern:

```text
https://cloud.google.com/blog/products/infrastructure/using-demand-response-to-reduce-data-center-power-consumption
```

This project should treat demand response as an offline simulation only.

## How To Run It

Planned command:

```bash
make demand-response
```

## Tests Or Validation To Perform

- Event-window filter test
- Target reduction calculation test
- Rebound accounting test
- Energy preservation test
- No negative simulated load test
- Unmet target test
- Dashboard helper query test

## Known Limitations

- Not a production optimizer.
- Not real-time grid control.
- Does not imply utility program participation.
- Estimated emissions impact should only be calculated when valid emissions factors exist for the event window.

## Next Steps

Implement after Feature 16 if emissions-aware event simulation is required. It can also be implemented with peak-only demand-response logic first.
