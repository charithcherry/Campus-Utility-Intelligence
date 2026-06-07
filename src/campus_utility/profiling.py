"""Raw dataset profiling utilities."""

from __future__ import annotations

import argparse
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from campus_utility.config import get_config

SUPPORTED_EXTENSIONS = {".csv", ".json", ".jsonl", ".parquet"}
TIMESTAMP_NAME_PARTS = ("time", "date", "timestamp", "datetime")


@dataclass(frozen=True)
class ColumnProfile:
    """Summary statistics for one column."""

    name: str
    dtype: str
    null_count: int
    null_rate: float


@dataclass(frozen=True)
class FileProfile:
    """Profile result for one raw data file."""

    path: Path
    row_count: int
    column_count: int
    duplicate_count: int
    columns: list[ColumnProfile]
    timestamp_coverage: dict[str, tuple[str, str]]
    sample_records: list[dict[str, object]]


def discover_raw_files(raw_dir: Path) -> list[Path]:
    """Return supported raw data files under the given directory."""

    if not raw_dir.exists():
        return []

    return sorted(
        path
        for path in raw_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def read_raw_file(path: Path) -> pd.DataFrame:
    """Read a supported raw file into a dataframe."""

    extension = path.suffix.lower()
    if extension == ".csv":
        return pd.read_csv(path)
    if extension == ".parquet":
        return pd.read_parquet(path)
    if extension == ".json":
        return pd.read_json(path)
    if extension == ".jsonl":
        return pd.read_json(path, lines=True)

    supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
    raise ValueError(f"Unsupported file extension '{extension}'. Supported: {supported}")


def profile_dataframe(path: Path, dataframe: pd.DataFrame, sample_size: int = 5) -> FileProfile:
    """Build a profile for a dataframe loaded from a raw file."""

    row_count = len(dataframe)
    columns = [
        ColumnProfile(
            name=str(column),
            dtype=str(dataframe[column].dtype),
            null_count=int(dataframe[column].isna().sum()),
            null_rate=float(dataframe[column].isna().mean()) if row_count else 0.0,
        )
        for column in dataframe.columns
    ]

    return FileProfile(
        path=path,
        row_count=row_count,
        column_count=len(dataframe.columns),
        duplicate_count=int(dataframe.duplicated().sum()),
        columns=columns,
        timestamp_coverage=detect_timestamp_coverage(dataframe),
        sample_records=dataframe.head(sample_size).where(pd.notna(dataframe), None).to_dict("records"),
    )


def detect_timestamp_coverage(dataframe: pd.DataFrame) -> dict[str, tuple[str, str]]:
    """Return min and max timestamp-like values for columns that parse as datetimes."""

    coverage: dict[str, tuple[str, str]] = {}
    for column in dataframe.columns:
        column_name = str(column)
        if not _looks_like_timestamp_column(column_name):
            continue

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            parsed = pd.to_datetime(dataframe[column], errors="coerce", utc=True)
        parsed = parsed.dropna()
        if parsed.empty:
            continue

        coverage[column_name] = (str(parsed.min()), str(parsed.max()))

    return coverage


def _looks_like_timestamp_column(column_name: str) -> bool:
    lower_name = column_name.lower()
    return any(part in lower_name for part in TIMESTAMP_NAME_PARTS)


def profile_raw_files(raw_dir: Path) -> list[FileProfile]:
    """Profile every supported raw file in a directory."""

    return [profile_dataframe(path, read_raw_file(path)) for path in discover_raw_files(raw_dir)]


def render_profile_report(raw_dir: Path, profiles: Iterable[FileProfile]) -> str:
    """Render a markdown report for raw dataset profiles."""

    profile_list = list(profiles)
    lines = [
        "# Raw Dataset Profile Report",
        "",
        f"Raw data directory: `{raw_dir}`",
        "",
    ]

    if not profile_list:
        lines.extend(
            [
                "No supported raw data files were found.",
                "",
                "Add Kaggle UNICON files under `data/raw/` and rerun:",
                "",
                "```bash",
                "make profile",
                "```",
                "",
                "Supported file types: `.csv`, `.json`, `.jsonl`, `.parquet`.",
            ]
        )
        return "\n".join(lines) + "\n"

    lines.extend([f"Profiled files: {len(profile_list)}", ""])
    for profile in profile_list:
        lines.extend(_render_file_profile(profile))

    return "\n".join(lines) + "\n"


def _render_file_profile(profile: FileProfile) -> list[str]:
    lines = [
        f"## {profile.path}",
        "",
        f"- Rows: {profile.row_count}",
        f"- Columns: {profile.column_count}",
        f"- Duplicate rows: {profile.duplicate_count}",
        "",
        "### Columns",
        "",
        "| Column | Type | Null Count | Null Rate |",
        "| --- | --- | ---: | ---: |",
    ]

    for column in profile.columns:
        lines.append(
            f"| {column.name} | {column.dtype} | {column.null_count} | {column.null_rate:.2%} |"
        )

    lines.extend(["", "### Timestamp Coverage", ""])
    if profile.timestamp_coverage:
        lines.extend(
            f"- `{column}`: {minimum} to {maximum}"
            for column, (minimum, maximum) in profile.timestamp_coverage.items()
        )
    else:
        lines.append("No parseable timestamp-like columns detected.")

    lines.extend(["", "### Sample Records", "", "```text"])
    if profile.sample_records:
        for record in profile.sample_records:
            lines.append(str(record))
    else:
        lines.append("No sample records available.")

    lines.extend(["```", ""])
    return lines


def write_profile_report(raw_dir: Path, output_path: Path) -> Path:
    """Profile raw files and write a markdown report."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    profiles = profile_raw_files(raw_dir)
    output_path.write_text(render_profile_report(raw_dir, profiles), encoding="utf-8")
    return output_path


def main() -> None:
    """CLI entry point for raw dataset profiling."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Profile raw campus utility data files.")
    parser.add_argument("--raw-dir", type=Path, default=config.raw_dir)
    parser.add_argument("--output", type=Path, default=Path("reports/profile_report.md"))
    args = parser.parse_args()

    report_path = write_profile_report(args.raw_dir, args.output)
    print(f"Wrote profile report to {report_path}")


if __name__ == "__main__":
    main()
