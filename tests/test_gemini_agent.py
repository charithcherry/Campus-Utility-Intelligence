import duckdb

from campus_utility.gemini_agent import (
    SYSTEM_PROMPT,
    get_tool_declarations,
    list_tables,
    retrieve_project_docs,
    run_gemini_agent,
    run_read_only_sql,
)


def test_system_prompt_has_accuracy_rules():
    assert "Do not invent" in SYSTEM_PROMPT
    assert "estimated Scope 2" in SYSTEM_PROMPT
    assert "offline simulations" in SYSTEM_PROMPT
    assert "fallback" in SYSTEM_PROMPT


def test_tool_declarations_include_required_tools():
    declarations = get_tool_declarations()[0]["functionDeclarations"]
    names = {declaration["name"] for declaration in declarations}

    assert names == {
        "retrieve_project_docs",
        "list_tables",
        "describe_table",
        "run_read_only_sql",
        "get_project_snapshot",
    }


def test_retrieve_project_docs_returns_sources(tmp_path):
    (tmp_path / "README.md").write_text(
        "# Campus Utility Intelligence\n\nDCCEEW Scope 2 emissions are estimated.",
        encoding="utf-8",
    )

    result = retrieve_project_docs("Scope 2 emissions", tmp_path)

    assert result["results"]
    assert result["results"][0]["source"] == "README.md"


def test_list_tables_and_read_only_sql(tmp_path):
    db_path = _create_agent_test_database(tmp_path)

    tables = list_tables(db_path)
    sql_result = run_read_only_sql(
        "SELECT COUNT(*) AS row_count FROM gold.gold_demand_response_simulation",
        db_path,
    )

    assert "gold_demand_response_simulation" in tables["tables"]["gold"]
    assert sql_result["rows"][0]["row_count"] == 1
    assert "LIMIT 50" in sql_result["sql"]


def test_run_read_only_sql_blocks_mutation(tmp_path):
    db_path = _create_agent_test_database(tmp_path)

    result = run_read_only_sql("DROP TABLE gold.gold_demand_response_simulation", db_path)

    assert "Only SELECT" in result["error"]
    assert result["rows"] == []


def test_gemini_agent_records_doc_and_sql_tool_trace(tmp_path, monkeypatch):
    db_path = _create_agent_test_database(tmp_path)
    (tmp_path / "README.md").write_text(
        "# Campus Utility Intelligence\n\nDemand response is an offline simulation.",
        encoding="utf-8",
    )
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.5-flash")
    responses = [
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "functionCall": {
                                    "name": "retrieve_project_docs",
                                    "args": {"query": "demand response", "top_k": 2},
                                }
                            },
                            {
                                "functionCall": {
                                    "name": "run_read_only_sql",
                                    "args": {
                                        "sql": (
                                            "SELECT COUNT(*) AS row_count "
                                            "FROM gold.gold_demand_response_simulation"
                                        )
                                    },
                                }
                            },
                        ]
                    }
                }
            ]
        },
        {"candidates": [{"content": {"parts": [{"text": "Final grounded answer."}]}}]},
    ]

    def fake_call(model, payload):
        assert model == "gemini-3.5-flash"
        assert payload["tools"]
        return responses.pop(0)

    monkeypatch.setattr("campus_utility.gemini_agent._call_gemini_api", fake_call)

    response = run_gemini_agent("Explain demand response and row count", tmp_path, db_path)

    assert response.answer == "Final grounded answer."
    assert [call.name for call in response.tool_calls] == [
        "retrieve_project_docs",
        "run_read_only_sql",
    ]
    assert response.sql_queries


def _create_agent_test_database(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    db_path.parent.mkdir(parents=True)
    with duckdb.connect(str(db_path)) as connection:
        connection.execute("CREATE SCHEMA gold")
        connection.execute(
            """
            CREATE TABLE gold.gold_demand_response_simulation (
                target_met BOOLEAN
            )
            """
        )
        connection.execute("INSERT INTO gold.gold_demand_response_simulation VALUES (TRUE)")
    return db_path
