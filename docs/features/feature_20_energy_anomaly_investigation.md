# Feature 20: Energy Anomaly Investigation

## Goal

Plan an investigation workflow that turns weather-normalized residuals into grouped anomaly candidates with clear explanation labels.

## Status

Planned. This feature is not implemented yet.

## Files Expected To Change

- `src/campus_utility/anomaly_investigation.py`
- `src/campus_utility/dashboard_data.py`
- `dashboard/app.py`
- `tests/test_anomaly_investigation.py`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/features/feature_20_energy_anomaly_investigation.md`
- `README.md`
- `Makefile`

## Implementation Details

Use existing `gold.gold_weather_normalized_usage` as the starting point.

Expected output table:

```text
gold.gold_energy_anomaly_candidates
```

Expected behavior:

- Rank anomalies by residual severity.
- Group by campus, source, meter, building, hour, and weekday/weekend.
- Add heuristic explanation labels.
- Add dashboard drilldown for top anomaly candidates.

Candidate labels:

- Weather-driven
- Overnight load
- Weekend load
- Sudden spike
- Missing data
- Reconciliation gap

## How To Run It

Planned command:

```bash
make anomalies
```

## Tests Or Validation To Perform

- Residual severity ranking test
- Candidate grouping test
- Label assignment test
- Candidate language check
- Dashboard helper query test

## Known Limitations

- Candidate labels are heuristics.
- Do not claim confirmed faults.
- Do not claim guaranteed savings.
- Facilities context is required before action.

## Next Steps

Consider only after Final Review Phase 3 if anomaly investigation becomes the priority.
