# Feature 8: SQL Analytics Queries

## Goal

Add reusable SQL analytics queries for usage, peak demand, and emissions outputs.

## Files Changed

- `Makefile`
- `README.md`
- `src/campus_utility/analytics.py`
- `tests/test_analytics.py`
- `sql/marts/top_monthly_usage.sql`
- `sql/marts/peak_demand_by_meter.sql`
- `sql/marts/monthly_emissions_summary.sql`
- `sql/marts/source_usage_summary.sql`
- `docs/features/feature_8_sql_analytics_queries.md`

## Implementation Details

The analytics workflow runs SQL files from `sql/marts/` against the DuckDB warehouse and writes markdown results under `reports/sql_analytics/`.

It also writes an index report to `reports/sql_analytics_report.md`.

## How To Run It

```bash
make analytics
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make analytics
```

## Known Limitations

The current queries are static report queries. They do not accept runtime filters yet.

## Next Steps

Implement the Streamlit dashboard.
