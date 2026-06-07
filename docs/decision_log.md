# Decision Log

## 2026-06-06: Use DuckDB for the local warehouse

DuckDB is the initial warehouse choice because it supports local analytical SQL workflows without requiring external infrastructure.

## 2026-06-06: Keep raw and generated data out of git

Raw Kaggle data, generated DuckDB files, and report outputs are ignored so the repository remains lightweight and does not commit large or local-only artifacts.

## 2026-06-06: Use Kaggle dataset `cdaclab/unicon`

The UNICON raw dataset was downloaded from Kaggle using the dataset slug `cdaclab/unicon`. Raw files are stored under `data/raw/` and remain uncommitted.

## 2026-06-06: Normalize timestamp parsing to UTC for profiling coverage

Some raw timestamp fields include timezone offsets while others do not. Profiling parses timestamp-like columns with `utc=True` only to compute coverage consistently. This does not define the final silver timestamp policy.

## 2026-06-06: Load bronze tables with DuckDB CSV inference

Bronze ingestion loads raw CSV files directly with DuckDB `read_csv_auto`. The loader treats `N/A` as null and uses full-file sampling because `building_submeter_consumption.csv` contains `N/A` values in columns that otherwise look numeric.

DuckDB inferred some bronze columns as `VARCHAR` where raw values are mixed. That is acceptable in bronze because cleaning and type enforcement belong in the silver layer.

## 2026-06-06: Keep silver electricity sources separate

Silver cleaning creates separate building, NMI, and submeter electricity tables. The raw sources have different grains and measurement columns, so combining them now would hide source-specific meaning.

Rows with missing required IDs, missing timestamps, missing consumption, or negative consumption are excluded from silver. Repeated meter/timestamp rows are deduplicated with `ROW_NUMBER`.

Submeter deduplication uses the normalized output timestamp because timezone-aware source timestamps can collapse to the same silver timestamp.

## 2026-06-06: Keep gold usage metrics source-aware

Gold usage metrics aggregate building, NMI, and submeter readings together only after keeping `source_system`. This avoids hiding differences in source grain while still supporting cross-source reporting.

Peak demand is calculated from NMI readings because NMI silver data includes `demand_kw` and `demand_kva`.

## 2026-06-06: Use configurable emissions factor

Estimated emissions multiply monthly electricity usage by `CAMPUS_ELECTRICITY_EMISSIONS_FACTOR_KG_CO2E_PER_UNIT`.

The default value is `0.79` kg CO2e per usage unit. This is treated as a configurable estimate, not an official project-specific factor.

## 2026-06-06: Store analytics queries as SQL files

Reusable analytics questions live in `sql/marts/` instead of being embedded only in Python. This keeps SQL visible for review and easier to reuse in dashboards later.
