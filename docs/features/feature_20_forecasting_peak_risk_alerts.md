# Feature 20: Forecasting And Peak-Risk Alerts

## Goal

Plan a forecasting layer that predicts future hourly electricity usage and identifies peak-risk windows.

## Status

Planned. This feature is not implemented yet.

## Files Expected To Change

- `src/campus_utility/forecasting.py`
- `src/campus_utility/dashboard_data.py`
- `dashboard/app.py`
- `tests/test_forecasting.py`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/features/feature_18_forecasting_peak_risk_alerts.md`
- `README.md`
- `Makefile`

## Implementation Details

Start simple:

- Seasonal naive baseline
- Lag-feature regression
- Rolling median baseline

Possible later models:

- SARIMA
- Prophet
- XGBoost or LightGBM
- Time-series foundation model benchmark

Expected output table:

```text
gold.gold_peak_risk_forecast
```

Expected fields:

```text
campus_id
source_system
meter_id
building_id
forecast_timestamp
predicted_consumption
prediction_interval_lower
prediction_interval_upper
peak_risk_flag
recommended_shift_window
model_version
backtest_error
```

## How To Run It

Planned command:

```bash
make forecast
```

## Tests Or Validation To Perform

- Time-order split test
- No future leakage test
- Forecast horizon test
- Backtest error calculation test
- Peak-risk threshold test
- Baseline comparison test

## Known Limitations

- Forecasting is not implemented.
- Do not claim production forecast quality without backtesting.
- Do not add complex models unless they beat simple baselines.
- Forecast recommendations are planning signals, not control actions.

## Next Steps

Consider only after Final Review Phase 3 if forecasting becomes the priority.
