SELECT
    campus_id,
    meter_id,
    peak_timestamp,
    peak_demand_kw,
    peak_demand_kva,
    consumption_at_peak
FROM gold.gold_peak_demand
ORDER BY peak_demand_kw DESC
LIMIT 20;
