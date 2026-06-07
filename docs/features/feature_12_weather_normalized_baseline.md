# Feature 12: Weather-Normalized Energy Baseline

## Goal

Use weather data to estimate expected electricity usage and identify high-usage candidates.

## Files Changed

- `Makefile`
- `README.md`
- `src/campus_utility/weather_baseline.py`
- `tests/test_weather_baseline.py`
- `docs/architecture.md`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/validation_rules.md`
- `docs/features/feature_12_weather_normalized_baseline.md`

## Implementation Details

The baseline workflow creates `gold.gold_weather_normalized_usage`.

It joins hourly electricity usage to hourly campus weather using real columns from `bronze.bronze_weather_data`: `campus_id`, `timestamp`, `air_temperature`, `apparent_temperature`, and `relative_humidity`.

The baseline is explainable. It calculates expected consumption using grouped medians by campus, source system, meter, optional building, hour of day, day of week, month, and 5-degree Celsius temperature band.

## How To Run It

```bash
make baseline
```

The report is written to:

```text
reports/weather_baseline_report.md
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make baseline
```

## Known Limitations

High-usage candidates are not confirmed waste, faults, or savings. They are records worth investigation.

The model is a simple grouped-median baseline, not a predictive machine-learning model.

## Next Steps

Implement Feature 13: peak-shifting simulator.
