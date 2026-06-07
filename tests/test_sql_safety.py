import duckdb
import pytest

from campus_utility.sql_safety import execute_readonly_query, validate_readonly_select


def test_validate_readonly_select_adds_default_limit():
    sql = validate_readonly_select("SELECT * FROM gold.gold_peak_demand")

    assert sql.endswith("LIMIT 50")


def test_validate_readonly_select_blocks_mutating_sql():
    with pytest.raises(ValueError, match="Only SELECT"):
        validate_readonly_select("DROP TABLE gold.gold_peak_demand")


def test_validate_readonly_select_allows_cte_query():
    sql = validate_readonly_select(
        """
        WITH example AS (
            SELECT 1 AS value
        )
        SELECT value FROM example
        """
    )

    assert sql.startswith("WITH example")
    assert sql.endswith("LIMIT 50")


def test_validate_readonly_select_blocks_multi_statement_sql():
    with pytest.raises(ValueError, match="Only one SQL statement"):
        validate_readonly_select("SELECT 1; SELECT 2")


def test_validate_readonly_select_allows_trailing_semicolon():
    sql = validate_readonly_select("SELECT 1 AS value;")

    assert sql == "SELECT 1 AS value LIMIT 50"


def test_execute_readonly_query_returns_dataframe(tmp_path):
    db_path = tmp_path / "processed" / "campus_utility.duckdb"
    db_path.parent.mkdir(parents=True)
    with duckdb.connect(str(db_path)) as connection:
        connection.execute("CREATE TABLE example AS SELECT 1 AS value")

    safe_sql, data = execute_readonly_query(db_path, "SELECT value FROM example")

    assert safe_sql == "SELECT value FROM example LIMIT 50"
    assert data["value"].iloc[0] == 1
