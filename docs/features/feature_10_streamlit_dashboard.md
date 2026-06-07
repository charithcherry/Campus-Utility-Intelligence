# Feature 10: Streamlit Dashboard

## Goal

Create a usable dashboard for the gold electricity analytics outputs.

## Files Changed

- `dashboard/app.py`
- `src/campus_utility/dashboard_data.py`
- `tests/test_dashboard_data.py`
- `README.md`
- `docs/features/feature_10_streamlit_dashboard.md`

## Implementation Details

The dashboard reads from DuckDB gold tables and shows:

- Monthly electricity usage
- Observed NMI peak demand
- Estimated monthly emissions
- NMI versus building reconciliation gaps

Sidebar filters allow selecting campuses and source systems.

## How To Run It

```bash
make dashboard
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
```

Dashboard data helper tests validate the DuckDB queries used by the app.

## Known Limitations

The dashboard is local only. It is not deployed and does not refresh automatically.

## Next Steps

Run the full pipeline and use the dashboard for manual review.
