"""Documentation-aware analytics copilot."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib import request

import pandas as pd

from campus_utility.config import get_config
from campus_utility.doc_index import SearchResult, build_document_index, search_document_index
from campus_utility.sql_safety import execute_readonly_query

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


@dataclass(frozen=True)
class CopilotResponse:
    """Copilot answer payload."""

    mode: str
    answer: str
    sources: list[SearchResult]
    sql: str | None
    data: pd.DataFrame | None
    used_model: str | None = None


def answer_question(question: str, project_root: Path, db_path: Path) -> CopilotResponse:
    """Answer a documentation or metric question."""

    metric_sql = _metric_question_to_sql(question)
    if metric_sql:
        safe_sql, data = execute_readonly_query(db_path, metric_sql)
        answer = _generate_metric_answer(question, safe_sql, data)
        return CopilotResponse(
            mode="metric",
            answer=answer,
            sources=[],
            sql=safe_sql,
            data=data,
            used_model=_configured_gemini_model() if _has_gemini_key() else None,
        )

    index = build_document_index(project_root)
    sources = search_document_index(question, index, limit=5)
    if not sources:
        return CopilotResponse(
            mode="documentation",
            answer=(
                "I could not find a relevant documentation source. Try asking about project "
                "architecture, emissions, weather baseline, simulations, dashboard pages, or tables."
            ),
            sources=[],
            sql=None,
            data=None,
        )

    snippets = _format_source_snippets(sources)
    answer = _generate_documentation_answer(question, snippets)
    return CopilotResponse(
        mode="documentation",
        answer=answer,
        sources=sources,
        sql=None,
        data=None,
        used_model=_configured_gemini_model() if _has_gemini_key() else None,
    )


def run_copilot_check(project_root: Path, db_path: Path) -> str:
    """Run a small deterministic copilot smoke check."""

    doc_response = answer_question("How are Scope 2 emissions estimated?", project_root, db_path)
    metric_response = answer_question(
        "How many demand-response scenarios met the target?",
        project_root,
        db_path,
    )
    if not doc_response.sources:
        raise RuntimeError("Copilot documentation check did not retrieve any sources")
    if metric_response.data is None or metric_response.data.empty:
        raise RuntimeError("Copilot metric check did not return data")
    return (
        "Copilot check passed\n"
        f"- documentation sources: {len(doc_response.sources)}\n"
        f"- metric rows: {len(metric_response.data)}"
    )


def _metric_question_to_sql(question: str) -> str | None:
    text = question.lower()
    table = _extract_table_name(text)
    if table and "row" in text:
        return f"SELECT COUNT(*) AS row_count FROM {table}"
    if "highest peak demand" in text or "top 10 peak-demand" in text or "top peak demand" in text:
        return """
            SELECT campus_id, meter_id, peak_timestamp, peak_demand_kw, peak_demand_kva
            FROM gold.gold_peak_demand
            ORDER BY peak_demand_kw DESC
            LIMIT 10
        """
    if "highest monthly usage" in text or "top monthly usage" in text:
        return """
            SELECT campus_id, source_system, usage_month, total_consumption
            FROM gold.gold_monthly_electricity_usage
            ORDER BY total_consumption DESC
            LIMIT 10
        """
    if "top high-usage" in text or "top high usage" in text:
        return """
            SELECT campus_id, source_system, meter_id, building_id, usage_hour,
                   actual_consumption, expected_consumption, residual_consumption,
                   efficiency_opportunity_score
            FROM gold.gold_weather_normalized_usage
            WHERE is_high_usage_candidate
            ORDER BY efficiency_opportunity_score DESC, residual_consumption DESC
            LIMIT 10
        """
    if "demand-response" in text and "met" in text:
        return """
            SELECT
                COUNT(*) AS simulated_events,
                COUNT(*) FILTER (WHERE target_met) AS events_meeting_target
            FROM gold.gold_demand_response_simulation
        """
    if "fallback_static_factor" in text or "fallback static factor" in text:
        return """
            SELECT factor_match_status, COUNT(*) AS row_count
            FROM gold.gold_hourly_time_varying_emissions
            GROUP BY factor_match_status
            ORDER BY factor_match_status
        """
    return None


def _extract_table_name(text: str) -> str | None:
    match = re.search(r"\b((?:gold|silver|bronze|reference)\.[a-zA-Z0-9_]+)\b", text)
    return match.group(1) if match else None


def _generate_documentation_answer(question: str, snippets: str) -> str:
    if not _has_gemini_key():
        return f"Relevant project documentation:\n\n{snippets}"
    prompt = (
        "Answer the user question using only the provided Campus Utility Intelligence "
        "documentation snippets. Be concise. If the snippets do not support an answer, say so.\n\n"
        f"Question: {question}\n\nDocumentation snippets:\n{snippets}"
    )
    return _call_gemini(prompt)


def _generate_metric_answer(question: str, sql: str, data: pd.DataFrame) -> str:
    preview = data.head(10).to_csv(index=False)
    if not _has_gemini_key():
        return "Answered with a safe read-only DuckDB query."
    prompt = (
        "Answer the metric question using only this SQL query and result preview. "
        "Do not invent extra values. Keep the answer concise.\n\n"
        f"Question: {question}\n\nSQL:\n{sql}\n\nResult preview:\n{preview}"
    )
    return _call_gemini(prompt)


def _format_source_snippets(sources: list[SearchResult]) -> str:
    return "\n\n".join(
        f"- {source.source_path} ({source.heading}): {source.text[:700]}"
        for source in sources[:5]
    )


def _has_gemini_key() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def _configured_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


def _call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    model = _configured_gemini_model()
    url = f"{GEMINI_API_URL.format(model=model)}?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 500,
        },
    }
    request_body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        url,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(http_request, timeout=20) as response:  # noqa: S310
        response_payload = json.loads(response.read().decode("utf-8"))
    candidates = response_payload.get("candidates", [])
    if not candidates:
        return "Gemini returned no answer."
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(part.get("text", "") for part in parts).strip()


def main() -> None:
    """CLI entry point for the copilot smoke check."""

    config = get_config()
    parser = argparse.ArgumentParser(description="Run analytics copilot smoke check.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--db-path", type=Path, default=config.db_path)
    args = parser.parse_args()

    print(run_copilot_check(args.project_root, args.db_path))


if __name__ == "__main__":
    main()
