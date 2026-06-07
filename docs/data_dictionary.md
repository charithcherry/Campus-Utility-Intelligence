# Data Dictionary

This dictionary documents raw source columns found by the Feature 2 profiling workflow. Final bronze, silver, and gold schemas will be documented when those layers are implemented.

## Raw Files

| File | Rows | Columns |
| --- | ---: | --- |
| `building_consumption.csv` | 8,095,524 | `campus_id`, `meter_id`, `timestamp`, `consumption` |
| `building_meta.csv` | 64 | `campus_id`, `id`, `built_year`, `category`, `gross_floor_area`, `room_area`, `capacity` |
| `building_submeter_consumption.csv` | 1,665,162 | `building_id`, `id`, `campus_id`, `timestamp`, `consumption`, `current`, `voltage`, `power`, `power_factor` |
| `calender.csv` | 2,312 | `date`, `is_holiday`, `is_semester`, `is_exam` |
| `campus_meta.csv` | 5 | `id`, `name`, `capacity` |
| `events.csv` | 106 | `meter_id`, `event_type`, `date`, `event_description` |
| `gas_consumption.csv` | 27,164 | `campus_id`, `timestamp`, `consumption` |
| `nmi_consumption.csv` | 3,507,076 | `campus_id`, `meter_id`, `timestamp`, `consumption`, `demand_kW`, `demand_kVA` |
| `nmi_meta.csv` | 14 | `id`, `campus_id`, `peak_demand` |
| `water_consumption.csv` | 245,040 | `campus_id`, `meter_id`, `timestamp`, `consumption` |
| `weather_data.csv` | 7,396,520 | `campus_id`, `timestamp`, `apparent_temperature`, `air_temperature`, `dew_point_temperature`, `relative_humidity`, `wind_speed`, `wind_direction` |

## Initial Electricity Candidates

The first implementation scope is electricity only. Based on raw profiling, likely electricity source files are:

- `building_consumption.csv`
- `building_submeter_consumption.csv`
- `nmi_consumption.csv`
- `building_meta.csv`
- `nmi_meta.csv`
- `campus_meta.csv`

No units are assumed yet. Unit meaning will be validated during bronze and silver implementation.

## Bronze Tables

Bronze tables are stored in `data/processed/campus_utility.duckdb` under the `bronze` schema.

| Bronze Table | Source File |
| --- | --- |
| `bronze.bronze_building_consumption` | `building_consumption.csv` |
| `bronze.bronze_building_meta` | `building_meta.csv` |
| `bronze.bronze_building_submeter_consumption` | `building_submeter_consumption.csv` |
| `bronze.bronze_calender` | `calender.csv` |
| `bronze.bronze_campus_meta` | `campus_meta.csv` |
| `bronze.bronze_events` | `events.csv` |
| `bronze.bronze_gas_consumption` | `gas_consumption.csv` |
| `bronze.bronze_nmi_consumption` | `nmi_consumption.csv` |
| `bronze.bronze_nmi_meta` | `nmi_meta.csv` |
| `bronze.bronze_water_consumption` | `water_consumption.csv` |
| `bronze.bronze_weather_data` | `weather_data.csv` |

DuckDB inferred source types during bronze ingestion. Final cleaned data types will be defined in silver.

## Silver Electricity Tables

| Silver Table | Grain | Key Columns |
| --- | --- | --- |
| `silver.silver_building_electricity_readings` | One building meter reading per campus, meter, and timestamp | `campus_id`, `meter_id`, `reading_timestamp` |
| `silver.silver_nmi_electricity_readings` | One NMI meter reading per campus, meter, and timestamp | `campus_id`, `meter_id`, `reading_timestamp` |
| `silver.silver_submeter_electricity_readings` | One submeter reading per campus, building, meter, and timestamp | `campus_id`, `building_id`, `meter_id`, `reading_timestamp` |

Common normalized columns include `campus_id`, `meter_id`, `reading_timestamp`, `consumption`, and `source_system`. NMI readings also include `demand_kw` and `demand_kva`. Submeter readings also include `current`, `voltage`, `power`, and `power_factor`.

## Gold Metric Tables

| Gold Table | Grain | Purpose |
| --- | --- | --- |
| `gold.gold_hourly_electricity_usage` | Campus, source, meter, optional building, and hour | Hourly usage trends and dashboard time series |
| `gold.gold_daily_electricity_usage` | Campus, source, and date | Daily usage summaries |
| `gold.gold_monthly_electricity_usage` | Campus, source, and month | Monthly usage summaries |
| `gold.gold_peak_demand` | Campus and NMI meter | Highest observed NMI demand |
| `gold.gold_electricity_emissions` | Campus, source, and month | Estimated emissions from monthly usage |
| `gold.gold_daily_nmi_building_reconciliation` | Campus and date | Daily NMI usage compared with summed building usage |
| `gold.gold_monthly_nmi_building_reconciliation` | Campus and month | Monthly NMI usage compared with summed building usage |
| `gold.gold_weather_normalized_usage` | Campus, source, meter, optional building, and hour | Actual vs expected usage after weather/time normalization |
| `gold.gold_peak_shift_simulation` | Campus, source, meter, optional building, date, and scenario | Offline same-day peak-shift simulation |

Reconciliation columns include NMI consumption, building consumption, absolute difference, and difference ratio to NMI. They do not identify the physical cause of the difference.

## Dashboard Views

The local dashboard reads from gold usage, peak-demand, emissions, and reconciliation tables. It does not create new data tables.

## Weather Baseline Columns

| Column | Meaning |
| --- | --- |
| `actual_consumption` | Observed hourly electricity usage |
| `expected_consumption` | Grouped median expected usage for similar weather/time conditions |
| `residual_consumption` | Actual minus expected usage |
| `residual_percent` | Residual divided by expected usage |
| `is_high_usage_candidate` | Flag for records at least 25% above expected usage |
| `efficiency_opportunity_score` | Bounded score from positive residual percent |
| `baseline_model_version` | Baseline method identifier |

## Peak Shift Simulation Columns

| Column | Meaning |
| --- | --- |
| `flexible_load_percent` | Requested flexible portion of peak-hour load |
| `baseline_peak_consumption` | Original peak hourly consumption |
| `simulated_peak_consumption` | Peak-hour consumption after shifting |
| `peak_reduction` | Difference between baseline and simulated peak hourly consumption |
| `peak_reduction_percent` | Peak reduction divided by baseline peak hourly consumption |
| `total_energy_preserved` | Whether daily energy is preserved |
| `negative_usage_created` | Whether simulation created invalid negative usage |

## Emissions Factor Reference

`reference.reference_emissions_factors` is loaded from CSV during `make emissions`.

| Column | Meaning |
| --- | --- |
| `factor_id` | Stable factor identifier |
| `country` | Factor country |
| `region` | Factor region |
| `source_system` | Matching source system or `*` wildcard |
| `energy_type` | Energy type, currently electricity |
| `factor_year` | Factor year |
| `emissions_factor_kg_co2e_per_kwh` | Emissions factor value |
| `factor_source_name` | Human-readable source name |
| `factor_source_url` | Source URL, if available |
| `is_default` | Whether this is a fallback/default factor |
| `notes` | Factor limitations or assumptions |

`gold.gold_electricity_emissions` stores the selected factor metadata on each emissions row.

## SQL Analytics Outputs

| Query | Purpose |
| --- | --- |
| `top_monthly_usage.sql` | Highest monthly usage records |
| `peak_demand_by_meter.sql` | Highest observed NMI demand records |
| `monthly_emissions_summary.sql` | Highest monthly estimated emissions records |
| `source_usage_summary.sql` | Total usage by source system |
