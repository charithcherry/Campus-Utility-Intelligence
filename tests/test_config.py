from pathlib import Path

from campus_utility.config import get_config


def test_get_config_uses_defaults(monkeypatch):
    monkeypatch.delenv("CAMPUS_UTILITY_RAW_DIR", raising=False)
    monkeypatch.delenv("CAMPUS_UTILITY_DB_PATH", raising=False)
    monkeypatch.delenv("CAMPUS_ELECTRICITY_EMISSIONS_FACTOR_KG_CO2E_PER_UNIT", raising=False)
    monkeypatch.delenv("CAMPUS_EMISSIONS_FACTORS_PATH", raising=False)
    monkeypatch.delenv("CAMPUS_GRID_CARBON_INTENSITY_PATH", raising=False)

    config = get_config()

    assert config.raw_dir == Path("data/raw")
    assert config.db_path == Path("data/processed/campus_utility.duckdb")
    assert config.electricity_emissions_factor_kg_co2e_per_unit == 0.79
    assert config.emissions_factors_path == Path("data/reference/emissions_factors_example.csv")
    assert config.grid_carbon_intensity_path == Path("data/reference/grid_carbon_intensity_hourly.csv")
