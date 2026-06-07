"""Gemini tool-calling analytics agent."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib import request

import duckdb
import pandas as pd

from campus_utility.doc_index import build_document_index, search_document_index
from campus_utility.sql_safety import execute_readonly_query

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_API_URL = f"{GEMINI_API_BASE_URL}/models/{{model}}:generateContent"
MAX_TOOL_TURNS = 8

SYSTEM_PROMPT = """You are the Campus Utility Intelligence Analyst, an expert in sustainability data engineering, campus utility analytics, energy efficiency, Scope 2 emissions estimation, weather-normalized baselines, peak-demand analysis, demand-response simulation, and DuckDB-based analytics marts.

You support only the Campus Utility Intelligence project.

You have access to project documentation through a retrieval tool and project metrics through safe read-only DuckDB SQL tools.

Rules:
- Do not invent metrics, tables, columns, emissions factors, or results.
- Use tools before answering questions that require project facts, table values, row counts, SQL results, or documentation details.
- For methodology questions, retrieve relevant project docs.
- For metric questions, inspect schemas and run safe read-only SQL.
- For mixed questions, retrieve docs and run SQL if needed.
- Explain assumptions and limitations clearly.
- Emissions are estimated Scope 2 values, not carbon accounting compliance.
- High-usage candidates are investigation candidates, not confirmed waste or faults.
- Peak-shifting and demand-response outputs are offline simulations, not proof of operational flexibility.
- If time-varying carbon-intensity data is missing, state that the project uses the static DCCEEW fallback factor.
- Never claim emissions-aware optimization unless real hourly carbon-intensity data is loaded.
- Include the SQL query used when answering metric questions.
- Include retrieved source file names when answering documentation questions.
- Once a SQL tool returns rows that answer the question, stop calling tools and provide the final answer.
- Keep answers concise, technical, and honest.
"""


@dataclass(frozen=True)
class ToolCallTrace:
    """Trace for a Gemini-requested tool call."""

    name: str
    arguments: dict
    result: dict


@dataclass(frozen=True)
class GeminiAgentResponse:
    """Final Gemini agent response and trace."""

    answer: str
    tool_calls: list[ToolCallTrace]
    model: str

    @property
    def sql_queries(self) -> list[str]:
        """Return SQL queries used by tool calls."""

        queries = []
        for call in self.tool_calls:
            if call.name == "run_read_only_sql":
                sql = call.result.get("sql") or call.arguments.get("sql")
                if sql:
                    queries.append(str(sql))
        return queries


def gemini_is_configured() -> bool:
    """Return whether Gemini mode can run."""

    return bool(os.getenv("GEMINI_API_KEY"))


def configured_gemini_model() -> str:
    """Return configured Gemini model."""

    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


def list_available_gemini_models() -> list[str]:
    """List available Gemini model names for the configured API key."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    payload = _call_gemini_models_api(api_key)
    return [
        model["name"].removeprefix("models/")
        for model in payload.get("models", [])
        if "generateContent" in model.get("supportedGenerationMethods", [])
    ]


def retrieve_project_docs(query: str, project_root: Path, top_k: int = 5) -> dict:
    """Retrieve relevant project documentation chunks."""

    index = build_document_index(project_root)
    results = search_document_index(query, index, limit=top_k)
    return {
        "query": query,
        "results": [
            {
                "source": result.source_path,
                "section": result.heading,
                "text": result.text[:1000],
                "score": result.score,
            }
            for result in results
        ],
    }


def list_tables(db_path: Path) -> dict:
    """List available DuckDB tables grouped by schema."""

    with duckdb.connect(str(db_path), read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema IN ('bronze', 'silver', 'gold', 'reference')
            ORDER BY table_schema, table_name
            """
        ).fetchall()
    tables: dict[str, list[str]] = {}
    for schema, table in rows:
        tables.setdefault(schema, []).append(table)
    return {"tables": tables}


def describe_table(table_name: str, db_path: Path) -> dict:
    """Describe a known DuckDB table."""

    schema, table = _validate_table_name(table_name, db_path)
    with duckdb.connect(str(db_path), read_only=True) as connection:
        columns = connection.execute(f"DESCRIBE {schema}.{table}").fetchall()
        row_count = connection.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]
    return {
        "table_name": f"{schema}.{table}",
        "row_count": row_count,
        "columns": [
            {"name": column[0], "type": column[1], "nullable": column[2]}
            for column in columns
        ],
    }


def run_read_only_sql(sql: str, db_path: Path, max_rows: int = 50) -> dict:
    """Execute safe read-only SQL and return preview rows."""

    try:
        safe_sql, data = execute_readonly_query(db_path, sql, default_limit=max_rows)
    except Exception as exc:  # noqa: BLE001 - returned as tool error for the model
        return {"error": str(exc), "sql": sql, "rows": [], "columns": [], "row_count": 0}
    preview = data.head(max_rows)
    return {
        "sql": safe_sql,
        "columns": list(preview.columns),
        "rows": _dataframe_rows(preview),
        "row_count": len(preview),
    }


def get_project_snapshot(db_path: Path) -> dict:
    """Return key project facts and limitations."""

    tables = list_tables(db_path)
    snapshot = {
        "tables": tables["tables"],
        "emissions_assumption": "Estimated Scope 2 using DCCEEW NGA 2025 Victoria factor 0.78 kg CO2-e/kWh.",
        "time_varying_carbon_limitation": "If reference.reference_grid_carbon_intensity_hourly has 0 rows, hourly emissions use fallback_static_factor and no emissions-aware optimization is claimed.",
        "weather_baseline_limitation": "High-usage candidates are investigation candidates, not confirmed waste or faults.",
        "simulation_limitation": "Peak-shifting and demand-response are offline simulations, not production optimizers or proof of operational flexibility.",
        "dashboard_pages": [
            "Executive Overview",
            "Usage Patterns",
            "Emissions",
            "Weather-Normalized Efficiency",
            "Peak-Shifting Simulator",
            "Grid Event Readiness",
            "Analytics Copilot",
            "NMI/Building Reconciliation",
            "Data Quality",
            "Methodology and Assumptions",
        ],
    }
    with duckdb.connect(str(db_path), read_only=True) as connection:
        for table in [
            "gold.gold_weather_normalized_usage",
            "gold.gold_hourly_time_varying_emissions",
            "reference.reference_grid_carbon_intensity_hourly",
            "gold.gold_demand_response_simulation",
        ]:
            schema, name = table.split(".")
            exists = connection.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = ? AND table_name = ?
                """,
                [schema, name],
            ).fetchone()[0]
            if exists:
                snapshot[f"{table}_rows"] = connection.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
    return snapshot


def run_gemini_agent(question: str, project_root: Path, db_path: Path) -> GeminiAgentResponse:
    """Run Gemini manual function-calling loop."""

    if not gemini_is_configured():
        raise RuntimeError("GEMINI_API_KEY is not configured")

    model = configured_gemini_model()
    contents = [
        {
            "role": "user",
            "parts": [{"text": f"{SYSTEM_PROMPT}\n\nUser question: {question}"}],
        }
    ]
    traces: list[ToolCallTrace] = []

    for _ in range(MAX_TOOL_TURNS):
        response = _call_gemini_api(
            model,
            {
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": contents,
                "tools": get_tool_declarations(),
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 900},
            },
        )
        function_calls = _extract_function_calls(response)
        if not function_calls:
            return GeminiAgentResponse(answer=_extract_text(response), tool_calls=traces, model=model)

        contents.append({"role": "model", "parts": [{"functionCall": call} for call in function_calls]})
        function_response_parts = []
        for call in function_calls:
            name = call["name"]
            args = call.get("args", {})
            result = _execute_tool(name, args, project_root, db_path)
            traces.append(ToolCallTrace(name=name, arguments=args, result=result))
            function_response_parts.append(
                {"functionResponse": {"name": name, "response": {"result": result}}}
            )
        contents.append({"role": "function", "parts": function_response_parts})

    return GeminiAgentResponse(
        answer="Gemini tool loop stopped after the maximum number of tool turns.",
        tool_calls=traces,
        model=model,
    )


def get_tool_declarations() -> list[dict]:
    """Return Gemini function declarations for the analytics agent."""

    return [
        {
            "functionDeclarations": [
                {
                    "name": "retrieve_project_docs",
                    "description": "Retrieve relevant chunks from README, docs, feature notes, final reviews, and local reports.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "top_k": {"type": "integer"},
                        },
                        "required": ["query"],
                    },
                },
                {
                    "name": "list_tables",
                    "description": "List available DuckDB tables grouped by schema.",
                    "parameters": {"type": "object", "properties": {}},
                },
                {
                    "name": "describe_table",
                    "description": "Describe a DuckDB table including columns, types, and row count.",
                    "parameters": {
                        "type": "object",
                        "properties": {"table_name": {"type": "string"}},
                        "required": ["table_name"],
                    },
                },
                {
                    "name": "run_read_only_sql",
                    "description": "Execute a safe read-only SELECT query against DuckDB.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql": {"type": "string"},
                            "max_rows": {"type": "integer"},
                        },
                        "required": ["sql"],
                    },
                },
                {
                    "name": "get_project_snapshot",
                    "description": "Return key project facts, table counts, assumptions, dashboard pages, and limitations.",
                    "parameters": {"type": "object", "properties": {}},
                },
            ]
        }
    ]


def _execute_tool(name: str, args: dict, project_root: Path, db_path: Path) -> dict:
    try:
        if name == "retrieve_project_docs":
            return retrieve_project_docs(args["query"], project_root, int(args.get("top_k", 5)))
        if name == "list_tables":
            return list_tables(db_path)
        if name == "describe_table":
            return describe_table(args["table_name"], db_path)
        if name == "run_read_only_sql":
            return run_read_only_sql(args["sql"], db_path, int(args.get("max_rows", 50)))
        if name == "get_project_snapshot":
            return get_project_snapshot(db_path)
        return {"error": f"Unknown tool: {name}"}
    except Exception as exc:  # noqa: BLE001 - tool errors are returned to the model
        return {"error": str(exc)}


def _call_gemini_api(model: str, payload: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    url = f"{GEMINI_API_URL.format(model=model)}?key={api_key}"
    http_request = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(http_request, timeout=30) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _call_gemini_models_api(api_key: str) -> dict:
    url = f"{GEMINI_API_BASE_URL}/models?key={api_key}"
    http_request = request.Request(
        url,
        headers={"Content-Type": "application/json"},
        method="GET",
    )
    with request.urlopen(http_request, timeout=30) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _extract_function_calls(response: dict) -> list[dict]:
    calls = []
    for part in _candidate_parts(response):
        if "functionCall" in part:
            calls.append(part["functionCall"])
    return calls


def _extract_text(response: dict) -> str:
    texts = [part.get("text", "") for part in _candidate_parts(response) if part.get("text")]
    return "\n".join(texts).strip() or "Gemini returned no final answer."


def _candidate_parts(response: dict) -> list[dict]:
    candidates = response.get("candidates", [])
    if not candidates:
        return []
    return candidates[0].get("content", {}).get("parts", [])


def _validate_table_name(table_name: str, db_path: Path) -> tuple[str, str]:
    if "." not in table_name:
        raise ValueError("Table name must include schema, such as gold.gold_peak_demand")
    schema, table = table_name.split(".", 1)
    if schema not in {"bronze", "silver", "gold", "reference"}:
        raise ValueError("Table schema is not allowed")
    if not schema.replace("_", "").isalnum() or not table.replace("_", "").isalnum():
        raise ValueError("Table name contains invalid characters")
    with duckdb.connect(str(db_path), read_only=True) as connection:
        exists = connection.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = ? AND table_name = ?
            """,
            [schema, table],
        ).fetchone()[0]
    if not exists:
        raise ValueError(f"Unknown table: {table_name}")
    return schema, table


def _dataframe_rows(data: pd.DataFrame) -> list[dict]:
    return json.loads(data.to_json(orient="records", date_format="iso"))
