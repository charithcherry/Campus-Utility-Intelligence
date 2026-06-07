# Feature 13: Peak-Shifting Simulator

## Goal

Estimate peak-demand reduction from offline same-day flexible load shifting.

## Files Changed

- `Makefile`
- `README.md`
- `src/campus_utility/peak_shift.py`
- `tests/test_peak_shift.py`
- `docs/architecture.md`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/validation_rules.md`
- `docs/features/feature_13_peak_shifting_simulator.md`

## Implementation Details

The simulator creates `gold.gold_peak_shift_simulation`.

It uses `gold.gold_hourly_electricity_usage`, identifies each campus/source/meter/building daily peak hour, and simulates shifting 5%, 10%, and 15% of that peak-hour load to the same day's lowest-load hour when the target is within the max shift window.

The workflow preserves total daily energy and prevents negative simulated peak usage.

## How To Run It

```bash
make simulate-shift
```

The report is written to:

```text
reports/peak_shift_report.md
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make simulate-shift
```

## Known Limitations

This is an offline analytical simulation, not a production optimizer. Hourly consumption is used as a peak-load proxy; this is not the same as measured NMI demand in `demand_kw`.

Because the project currently uses a static DCCEEW Victoria Scope 2 emissions factor, same-day shifting preserves total estimated emissions when total kWh is preserved. The simulator does not claim emissions reduction.

## Next Steps

Implement Feature 14: dashboard extensions for baseline and simulation views.
