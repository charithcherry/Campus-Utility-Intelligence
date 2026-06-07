SELECT
    campus_id,
    source_system,
    usage_month,
    total_consumption,
    emissions_factor_kg_co2e_per_kwh,
    estimated_emissions_kg_co2e
FROM gold.gold_electricity_emissions
ORDER BY estimated_emissions_kg_co2e DESC
LIMIT 20;
