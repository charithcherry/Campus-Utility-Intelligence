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

## 2026-06-07: Load emissions factors from reference data

Feature 11 replaces the single numeric-only emissions factor workflow with a CSV-backed reference table. The included CSV uses the DCCEEW 2025 National Greenhouse Accounts Factors Victoria location-based purchased electricity Scope 2 factor of `0.78 kg CO2-e/kWh`.

Factor selection prefers source-specific matches over wildcard matches and exact-year factors over older factors. Missing source-specific factors fall back to a documented default factor when available.

The preferred official source for a static Australia factor is DCCEEW's National Greenhouse Accounts Factors. Time-varying grid emissions intensity may be considered later with sources such as Open Electricity or CSIRO. The repository currently ships a verified DCCEEW Victoria Scope 2 factor, not CSIRO or Open Electricity data.

The DCCEEW 2025 Victoria Scope 2 factor is used as the project default across historical usage years because year-specific historical factors are not included in the repository.

## 2026-06-07: Use grouped median weather baseline

Feature 12 uses an explainable grouped median baseline instead of a black-box model. Expected usage is grouped by campus, source, meter, optional building, hour of day, day of week, month, and 5-degree Celsius temperature band.

High-usage candidates are investigation leads, not confirmed waste, faults, or savings.

## 2026-06-07: Treat peak shifting as an offline peak-consumption simulation

Feature 13 uses hourly consumption as a peak-load proxy and shifts load only within the same day and same campus/source/meter/building group.

Because the project uses a static DCCEEW Victoria Scope 2 emissions factor, preserved daily kWh means estimated emissions remain unchanged. The simulator does not claim emissions reduction.

## 2026-06-06: Store analytics queries as SQL files

Reusable analytics questions live in `sql/marts/` instead of being embedded only in Python. This keeps SQL visible for review and easier to reuse in dashboards later.

## 2026-06-06: Reconcile NMI and building usage at campus level

NMI readings include `campus_id` and `meter_id`, but not `building_id`. Reconciliation compares campus-level NMI totals against summed campus-level building meter totals.

Differences are treated as diagnostics, not automatic corruption, because NMI and building meters may have different coverage.

The dataset can quantify NMI/building differences, but it cannot directly attribute those differences to specific load categories such as street lighting or outdoor infrastructure because those labels are not present in the current reconciliation inputs.

## 2026-06-06: Keep dashboard local

The dashboard runs locally with Streamlit and reads from the DuckDB warehouse. It is not deployed and does not claim real-time refresh.
