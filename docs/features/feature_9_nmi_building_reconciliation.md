# Feature 9: NMI Building Reconciliation

## Goal

Compare campus-level NMI electricity usage against summed campus-level building meter usage.

## Files Changed

- `Makefile`
- `README.md`
- `src/campus_utility/reconciliation.py`
- `tests/test_reconciliation.py`
- `docs/architecture.md`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `docs/features/feature_9_nmi_building_reconciliation.md`

## Implementation Details

The reconciliation workflow creates:

- `gold.gold_daily_nmi_building_reconciliation`
- `gold.gold_monthly_nmi_building_reconciliation`

It compares NMI totals to building totals by campus and date/month. It does not compare NMI to individual buildings because NMI data has no `building_id`.

## How To Run It

```bash
make reconcile
```

The report is written to:

```text
reports/reconciliation_report.md
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make reconcile
```

## Known Limitations

Differences do not automatically mean corruption. NMI and building meters may measure different coverage.

The current data does not contain a column that labels the difference as street lighting, outdoor loads, shared infrastructure, losses, or another specific cause. The reconciliation can quantify the gap, but it cannot fully allocate the gap source from the available columns.

Initial real-data result: 140 monthly campus periods had both NMI and building usage. The largest observed monthly gap was campus `1` in March 2022, where NMI usage was `2,220,571.448`, building usage was `1,552,068.85259`, and the difference was about `668,502.595`.

Likely explanations include outdoor lighting, parking or street lighting, central plant loads, shared infrastructure, unmetered loads, electrical losses, incomplete building-meter coverage, or timestamp/interval mismatch.

## Next Steps

Use reconciliation outputs in dashboard views or deeper diagnostics.
