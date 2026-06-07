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
