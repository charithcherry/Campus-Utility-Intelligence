from pathlib import Path

from campus_utility.config import get_config


def test_get_config_uses_defaults(monkeypatch):
    monkeypatch.delenv("CAMPUS_UTILITY_RAW_DIR", raising=False)
    monkeypatch.delenv("CAMPUS_UTILITY_DB_PATH", raising=False)

    config = get_config()

    assert config.raw_dir == Path("data/raw")
    assert config.db_path == Path("data/processed/campus_utility.duckdb")
