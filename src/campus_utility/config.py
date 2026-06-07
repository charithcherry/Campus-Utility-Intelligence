"""Configuration helpers for local project paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    """Filesystem configuration for local runs."""

    raw_dir: Path
    db_path: Path


def get_config() -> ProjectConfig:
    """Return project configuration from environment variables or defaults."""

    return ProjectConfig(
        raw_dir=Path(os.getenv("CAMPUS_UTILITY_RAW_DIR", "data/raw")),
        db_path=Path(os.getenv("CAMPUS_UTILITY_DB_PATH", "data/processed/campus_utility.duckdb")),
    )
