import duckdb

from campus_utility.copilot import answer_question, run_copilot_check


def test_answer_question_routes_metric_question_to_safe_sql(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    db_path = _create_copilot_test_database(tmp_path)

    response = answer_question(
        "How many demand-response scenarios met the target?",
        tmp_path,
        db_path,
    )

    assert response.mode == "metric"
    assert response.sql is not None
    assert "gold.gold_demand_response_simulation" in response.sql
    assert response.data is not None
    assert response.data["events_meeting_target"].iloc[0] == 1


def test_answer_question_routes_documentation_question_to_sources(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    db_path = _create_copilot_test_database(tmp_path)
    (tmp_path / "README.md").write_text(
        "# Campus Utility Intelligence\n\nScope 2 emissions use a DCCEEW factor.",
        encoding="utf-8",
    )

    response = answer_question("How are Scope 2 emissions estimated?", tmp_path, db_path)

    assert response.mode == "documentation"
    assert response.sources
    assert "README.md" in response.answer


def test_answer_question_uses_configured_gemini_for_docs(tmp_path, monkeypatch):
    db_path = _create_copilot_test_database(tmp_path)
    (tmp_path / "README.md").write_text(
        "# Campus Utility Intelligence\n\nScope 2 emissions use a DCCEEW factor.",
        encoding="utf-8",
    )
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.5-flash")
    monkeypatch.setattr("campus_utility.copilot._call_gemini", lambda prompt: "Gemini answer")

    response = answer_question("How are Scope 2 emissions estimated?", tmp_path, db_path)

    assert response.answer == "Gemini answer"
    assert response.used_model == "gemini-3.5-flash"


def test_run_copilot_check_passes(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    db_path = _create_copilot_test_database(tmp_path)
    (tmp_path / "README.md").write_text(
        "# Campus Utility Intelligence\n\nScope 2 emissions use a DCCEEW factor.",
        encoding="utf-8",
    )

    result = run_copilot_check(tmp_path, db_path)

    assert "Copilot check passed" in result


def _create_copilot_test_database(tmp_path):
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
