# Feature 19: Documentation-Aware Analytics Copilot

## Goal

Add a lightweight analytics copilot that combines project-document retrieval with safe read-only DuckDB queries for metric questions.

## Status

Implemented.

## Files Changed

- `src/campus_utility/doc_index.py`
- `src/campus_utility/sql_safety.py`
- `src/campus_utility/copilot.py`
- `tests/test_doc_index.py`
- `tests/test_sql_safety.py`
- `tests/test_copilot.py`
- `dashboard/app.py`
- `.env.example`
- `Makefile`
- `README.md`
- `docs/architecture.md`
- `docs/decision_log.md`
- `docs/features/feature_19_analytics_copilot.md`
- `docs/phase_3_plan.md`

## Implementation Details

The copilot supports two paths:

- Documentation questions use a lightweight local retriever over README, docs, feature notes, final reviews, and local generated markdown reports when present.
- Metric questions use predefined safe read-only DuckDB SQL routes.

The copilot does not embed raw electricity rows. Raw, silver, and gold data stay in DuckDB.

Gemini integration was upgraded in Feature 20. The current implementation routes Gemini-enabled questions through a tool-calling agent. If no key is configured, the copilot returns extractive local answers and predefined safe SQL metric results.

## SQL Safety

The SQL layer:

- Allows only single `SELECT` statements.
- Blocks mutating or destructive tokens.
- Blocks multi-statement SQL.
- Adds a default `LIMIT` when missing.
- Shows the SQL used in dashboard responses.

## Dashboard

The Streamlit dashboard now includes:

```text
Analytics Copilot
```

The page shows:

- Answer text
- Retrieved documentation sources
- SQL query used for metric answers
- Query result preview
- Gemini model used, when configured

## How To Run It

```bash
make copilot-check
make dashboard
```

Optional local environment variables:

```bash
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
```

Do not commit API keys.

## Tests Or Validation Performed

Run:

```bash
make test
make lint
make copilot-check
make dashboard
```

Automated tests cover:

- Document indexing
- Documentation retrieval
- SQL safety
- Metric question routing
- Documentation question routing
- Gemini configuration path without calling the real API

## Known Limitations

- The copilot is not production-ready.
- It does not answer every possible question.
- It uses predefined metric routes, not arbitrary natural-language-to-SQL.
- Gemini output is optional and only summarizes retrieved docs or SQL outputs.
- Raw meter rows are not embedded.

## Next Steps

Stop for approval. Optional later work could expand metric routes or add a richer local retriever.
