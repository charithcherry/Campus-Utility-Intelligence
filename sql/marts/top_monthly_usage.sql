SELECT
    campus_id,
    source_system,
    usage_month,
    total_consumption,
    reading_count,
    max_daily_meter_count
FROM gold.gold_monthly_electricity_usage
ORDER BY total_consumption DESC
LIMIT 20;
