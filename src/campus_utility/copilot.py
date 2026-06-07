"""Documentation-aware analytics copilot."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from campus_utility.config import get_config
from campus_utility.doc_index import SearchResult, build_document_index, search_document_index
from campus_utility.gemini_agent import (
    ToolCallTrace,
    gemini_is_configured,
    run_gemini_agent,
)
from campus_utility.sql_safety import execute_readonly_query


@dataclass(frozen=True)
class CopilotResponse:
    """Copilot answer payload."""

    mode: str
    answer: str
    sources: list[SearchResult]
    sql: str | None
    data: pd.DataFrame | None
    used_model: str | None = None
    tool_calls: list[ToolCallTrace] | None = None
    gemini_enabled: bool = False
    fallback_reason: str | None = None


def answer_question(question: str, project_root: Path, db_path: Path) -> CopilotResponse:
    """Answer a documentation or metric question."""

    fallback_reason = "Gemini mode disabled because GEMINI_API_KEY is not configured."
    if gemini_is_configured():
        try:
            agent_response = run_gemini_agent(question, project_root, db_path)
            return CopilotResponse(
                mode="gemini_tool_agent",
                answer=agent_response.answer,
                sources=_sources_from_tool_calls(agent_response.tool_calls),
                sql="\n\n".join(agent_response.sql_queries) or None,
                data=_first_sql_dataframe(agent_response.tool_calls),
                used_model=agent_response.model,
                tool_calls=agent_response.tool_calls,
                gemini_enabled=True,
            )
        except Exception as exc:  # noqa: BLE001 - fallback keeps dashboard usable
            fallback_reason = f"Gemini tool agent failed: {exc}"

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
            used_model=None,
            gemini_enabled=False,
            fallback_reason=fallback_reason,
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
            gemini_enabled=False,
            fallback_reason=fallback_reason,
        )

    snippets = _format_source_snippets(sources)
    answer = _generate_documentation_answer(question, snippets)
    return CopilotResponse(
        mode="documentation",
        answer=answer,
        sources=sources,
        sql=None,
        data=None,
        used_model=None,
        gemini_enabled=False,
        fallback_reason=fallback_reason,
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
    _ = question
    return f"Relevant project documentation:\n\n{snippets}"


def _generate_metric_answer(question: str, sql: str, data: pd.DataFrame) -> str:
    _ = question, sql, data
    return "Answered with a safe read-only DuckDB query."


def _format_source_snippets(sources: list[SearchResult]) -> str:
    return "\n\n".join(
        f"- {source.source_path} ({source.heading}): {source.text[:700]}"
        for source in sources[:5]
    )


def _sources_from_tool_calls(tool_calls: list[ToolCallTrace]) -> list[SearchResult]:
    sources: list[SearchResult] = []
    for call in tool_calls:
        if call.name != "retrieve_project_docs":
            continue
        for result in call.result.get("results", []):
            sources.append(
                SearchResult(
                    source_path=result["source"],
                    heading=result["section"],
                    text=result["text"],
                    score=float(result.get("score", 0)),
                )
            )
    return sources


def _first_sql_dataframe(tool_calls: list[ToolCallTrace]) -> pd.DataFrame | None:
    for call in tool_calls:
        if call.name != "run_read_only_sql":
            continue
        rows = call.result.get("rows", [])
        if rows:
            return pd.DataFrame(rows)
    return None


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
