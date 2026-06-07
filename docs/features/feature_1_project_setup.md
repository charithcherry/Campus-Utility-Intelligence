# Feature 1: Project Setup

## Goal

Create the base project structure for a local Python, SQL, DuckDB, and Streamlit analytics project.

## Files Changed

- `.gitignore`
- `.env.example`
- `pyproject.toml`
- `Makefile`
- `src/campus_utility/__init__.py`
- `src/campus_utility/config.py`
- `src/campus_utility/logging_utils.py`
- `dashboard/app.py`
- `tests/test_config.py`
- `docs/architecture.md`
- `docs/data_dictionary.md`
- `docs/validation_rules.md`
- `docs/decision_log.md`
- `docs/features/feature_1_project_setup.md`
- `README.md`

## Implementation Details

The feature adds the initial repository layout, Python package metadata, local configuration helpers, a placeholder Streamlit app, and basic documentation placeholders.

Raw data, generated databases, reports, caches, virtual environments, and local environment files are gitignored.

This setup was needed so later data work has repeatable commands, clear folders, ignored local artifacts, and a tested Python package structure.

## How To Run It

Install dependencies:

```bash
make install
```

The Makefile creates `.venv` with `python3.12` by default. Override it with `make SYSTEM_PYTHON=/path/to/python install` if needed.

Run tests:

```bash
make test
```

Open the placeholder dashboard:

```bash
make dashboard
```

## Tests Or Validation Performed

Validation for this feature includes checking the project structure and running `make test`.

## Known Limitations

No Kaggle data profiling, ingestion, transformations, analytics marts, quality checks, or completed dashboard views are implemented yet.

## Next Steps

Implement Feature 2: Dataset Setup and Profiling.
