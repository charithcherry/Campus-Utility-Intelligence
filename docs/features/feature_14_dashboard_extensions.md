# Feature 14: Dashboard Extensions

## Goal

Expose Phase 2 decision-support outputs in the local Streamlit dashboard.

## Files Changed

- `dashboard/app.py`
- `src/campus_utility/dashboard_data.py`
- `tests/test_dashboard_data.py`
- `README.md`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/features/feature_14_dashboard_extensions.md`

## Implementation Details

The dashboard now includes:

- Emissions assumptions using the DCCEEW NGA 2025 Victoria Scope 2 factor
- Weather-normalized high-usage candidate summaries
- Top weather-normalized investigation candidates
- Peak-shifting simulation summaries
- Top peak-reduction scenarios

Existing usage, peak demand, emissions, and reconciliation views remain available.

Optional Phase 2 tables are checked before loading so the dashboard does not crash if they are missing.

## How To Run It

```bash
make dashboard
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make dashboard
```

## Known Limitations

The dashboard is local only and not deployed.

High-usage candidates are investigation candidates, not confirmed waste or faults.

Peak shifting is an offline simulation, not a production optimizer. It does not claim emissions reduction under the current static emissions factor.

## Next Steps

Run Phase 2 final review.
