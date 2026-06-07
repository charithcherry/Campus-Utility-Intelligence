# Feature 2: Dataset Setup and Profiling

## Goal

Add a reproducible profiling workflow for raw Kaggle UNICON campus utility files without assuming the source schema.

## Files Changed

- `Makefile`
- `README.md`
- `docs/data_dictionary.md`
- `docs/decision_log.md`
- `src/campus_utility/profiling.py`
- `tests/test_profiling.py`
- `docs/features/feature_2_dataset_setup_and_profiling.md`

## Implementation Details

The profiling workflow scans `data/raw/` recursively for supported raw file types:

- `.csv`
- `.json`
- `.jsonl`
- `.parquet`

For each file, it records row counts, column counts, column names, pandas data types, null counts, null rates, duplicate row counts, timestamp coverage for timestamp-like columns, and a small sample of records.

The workflow writes a markdown report to `reports/profile_report.md`. Reports are generated artifacts and are not committed to git.

The feature also adds a Kaggle download command for the UNICON dataset slug `cdaclab/unicon`.

The downloaded raw dataset contains 11 CSV files and uses about 907 MB locally.

## How To Run It

Place Kaggle UNICON files under `data/raw/`, then run:

```bash
make download-data
```

This requires Kaggle API credentials at `~/.kaggle/kaggle.json`.

Then profile the raw files:

```bash
make profile
```

The report will be written to:

```text
reports/profile_report.md
```

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make download-data
make profile
```

Validation completed successfully with real downloaded raw data.

## Known Limitations

Timestamp detection is intentionally conservative and only checks columns with names containing `time`, `date`, `timestamp`, or `datetime`.

The profiling workflow reads each supported file into memory. This is acceptable for the current 907 MB local dataset but may need chunking for larger future datasets.

## Next Steps

Add raw Kaggle files under `data/raw/`, run profiling, then implement Feature 3: Bronze Ingestion.
