# Decision Log

## 2026-06-06: Use DuckDB for the local warehouse

DuckDB is the initial warehouse choice because it supports local analytical SQL workflows without requiring external infrastructure.

## 2026-06-06: Keep raw and generated data out of git

Raw Kaggle data, generated DuckDB files, and report outputs are ignored so the repository remains lightweight and does not commit large or local-only artifacts.

## 2026-06-06: Use Kaggle dataset `cdaclab/unicon`

The UNICON raw dataset was downloaded from Kaggle using the dataset slug `cdaclab/unicon`. Raw files are stored under `data/raw/` and remain uncommitted.

## 2026-06-06: Normalize timestamp parsing to UTC for profiling coverage

Some raw timestamp fields include timezone offsets while others do not. Profiling parses timestamp-like columns with `utc=True` only to compute coverage consistently. This does not define the final silver timestamp policy.
