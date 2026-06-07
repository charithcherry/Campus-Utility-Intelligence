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

## Next Steps

Use reconciliation outputs in dashboard views or deeper diagnostics.
