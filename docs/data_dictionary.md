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
