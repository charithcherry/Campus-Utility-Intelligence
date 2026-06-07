"""Lightweight documentation index for the analytics copilot."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DOC_PATHS = (
    "README.md",
    "docs/architecture.md",
    "docs/data_dictionary.md",
    "docs/validation_rules.md",
    "docs/decision_log.md",
    "docs/final_review.md",
    "docs/final_review_phase_2.md",
    "docs/final_review_phase_3.md",
    "docs/phase_2_plan.md",
    "docs/phase_3_plan.md",
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "for",
    "from",
    "how",
    "in",
    "is",
    "of",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "why",
}


@dataclass(frozen=True)
class DocumentChunk:
    """One searchable documentation chunk."""

    source_path: str
    heading: str
    text: str


@dataclass(frozen=True)
class SearchResult:
    """One retrieved documentation result."""

    source_path: str
    heading: str
    text: str
    score: int


def build_document_index(project_root: Path, include_reports: bool = True) -> list[DocumentChunk]:
    """Build an in-memory index from project documentation."""

    chunks: list[DocumentChunk] = []
    for path in _collect_doc_paths(project_root, include_reports):
        chunks.extend(_chunk_markdown(path, project_root))
    return chunks


def search_document_index(
    query: str,
    index: list[DocumentChunk],
    limit: int = 5,
) -> list[SearchResult]:
    """Return top documentation chunks for a query."""

    query_terms = _tokenize(query)
    if not query_terms:
        return []

    scored = []
    for chunk in index:
        chunk_terms = _tokenize(f"{chunk.heading} {chunk.text}")
        score = sum(1 for term in query_terms if term in chunk_terms)
        if score:
            scored.append(
                SearchResult(
                    source_path=chunk.source_path,
                    heading=chunk.heading,
                    text=chunk.text,
                    score=score,
                )
            )
    return sorted(scored, key=lambda result: result.score, reverse=True)[:limit]


def _collect_doc_paths(project_root: Path, include_reports: bool) -> list[Path]:
    paths = [project_root / relative for relative in DEFAULT_DOC_PATHS]
    features_dir = project_root / "docs" / "features"
    if features_dir.exists():
        paths.extend(sorted(features_dir.glob("*.md")))
    reports_dir = project_root / "reports"
    if include_reports and reports_dir.exists():
        paths.extend(sorted(reports_dir.rglob("*.md")))
    return [path for path in paths if path.exists() and path.is_file()]


def _chunk_markdown(path: Path, project_root: Path) -> list[DocumentChunk]:
    relative_path = str(path.relative_to(project_root))
    text = path.read_text(encoding="utf-8")
    chunks: list[DocumentChunk] = []
    heading = "Overview"
    buffer: list[str] = []

    for line in text.splitlines():
        if line.startswith("#"):
            if buffer:
                chunks.extend(_paragraph_chunks(relative_path, heading, "\n".join(buffer)))
                buffer = []
            heading = line.lstrip("#").strip() or "Overview"
        else:
            buffer.append(line)
    if buffer:
        chunks.extend(_paragraph_chunks(relative_path, heading, "\n".join(buffer)))
    return chunks


def _paragraph_chunks(source_path: str, heading: str, text: str) -> list[DocumentChunk]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    return [
        DocumentChunk(source_path=source_path, heading=heading, text=paragraph)
        for paragraph in paragraphs
    ]


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9_]+", text.lower())
        if token not in STOPWORDS and len(token) > 1
    }
