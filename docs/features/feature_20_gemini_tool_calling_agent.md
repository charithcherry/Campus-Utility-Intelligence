# Feature 20: Gemini Tool-Calling Analytics Agent

## Goal

Upgrade the analytics copilot from simple retrieval and SQL routing into a Gemini tool-calling agent that can decide when to retrieve project docs, inspect DuckDB tables, and run safe read-only SQL.

## Files Changed

- `src/campus_utility/gemini_agent.py`
- `src/campus_utility/copilot.py`
- `src/campus_utility/sql_safety.py`
- `dashboard/app.py`
- `tests/test_gemini_agent.py`
- `tests/test_copilot.py`
- `tests/test_sql_safety.py`
- `README.md`
- `docs/architecture.md`
- `docs/decision_log.md`
- `docs/phase_3_plan.md`

## Implementation

The Gemini agent exposes five local tools:

```text
retrieve_project_docs(query, top_k)
list_tables()
describe_table(table_name)
run_read_only_sql(sql, max_rows)
get_project_snapshot()
```

When `GEMINI_API_KEY` is configured, dashboard copilot questions go through Gemini. Gemini can call the tools for project docs, table metadata, and safe SQL results before producing a final answer.

When `GEMINI_API_KEY` is missing or Gemini fails, the copilot falls back to the existing local retrieval and predefined metric-query behavior.

## Safety Rules

- API keys must stay in local environment variables only.
- The project must not commit Gemini API keys.
- SQL is read-only and limited to one `SELECT` or `WITH ... SELECT` statement.
- Mutating SQL tokens such as `DROP`, `DELETE`, `INSERT`, `UPDATE`, `CREATE`, `COPY`, and `CALL` are blocked.
- Raw meter rows are not embedded into the documentation index.
- Gemini must not invent metrics, emissions factors, row counts, tables, or conclusions.

## Dashboard Outcome

The `Analytics Copilot` page now shows:

- Gemini tool-calling mode status
- final answer
- tool calls made
- SQL used
- result preview
- retrieved sources
- safety and limitation notes
- local fallback message when Gemini is unavailable

## Validation

Expected commands:

```bash
make test
make lint
make copilot-check
make dashboard
```

## Limitations

This is a local analytics assistant, not a production BI agent. It depends on the local DuckDB file and local project docs. Gemini answers are only as reliable as the retrieved docs and SQL tool outputs.
