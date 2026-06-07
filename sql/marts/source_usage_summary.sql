SELECT
    source_system,
    COUNT(*) AS monthly_rows,
    SUM(total_consumption) AS total_consumption,
    SUM(reading_count) AS total_readings
FROM gold.gold_monthly_electricity_usage
GROUP BY source_system
ORDER BY total_consumption DESC;
