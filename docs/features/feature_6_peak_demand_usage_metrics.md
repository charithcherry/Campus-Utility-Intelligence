# Feature 6: Peak-Demand and Usage Metrics

## Goal

Create gold electricity usage and peak-demand metric tables from cleaned silver data.

## Files Changed

- `Makefile`
- `README.md`
- `src/campus_utility/metrics.py`
- `tests/test_metrics.py`
- `docs/architecture.md`
- `docs/data_dictionary.md`
- `docs/features/feature_6_peak_demand_usage_metrics.md`

## Implementation Details

The metrics workflow creates four gold tables:

- `gold.gold_hourly_electricity_usage`
- `gold.gold_daily_electricity_usage`
- `gold.gold_monthly_electricity_usage`
- `gold.gold_peak_demand`

Usage metrics aggregate consumption from building, NMI, and submeter silver readings. Peak demand uses NMI `demand_kw` and keeps one peak row per campus and meter.

## How To Run It

```bash
make metrics
```

The metrics report is written to:

```text
reports/gold_metrics_report.md
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make metrics
```

## Known Limitations

Gold metrics are source-aware but do not yet join building metadata, calculate emissions, or power dashboard views.

## Next Steps

Implement estimated emissions metrics.
