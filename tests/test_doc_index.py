from campus_utility.doc_index import build_document_index, search_document_index


def test_build_document_index_reads_project_docs(tmp_path):
    readme = tmp_path / "README.md"
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "architecture.md").write_text("# Architecture\n\nDuckDB warehouse.", encoding="utf-8")
    readme.write_text("# Project\n\nScope 2 emissions are estimated.", encoding="utf-8")

    index = build_document_index(tmp_path, include_reports=False)
    results = search_document_index("Scope 2 emissions", index)

    assert index
    assert results[0].source_path == "README.md"


def test_search_document_index_returns_empty_for_unmatched_query(tmp_path):
    (tmp_path / "README.md").write_text("# Project\n\nDuckDB warehouse.", encoding="utf-8")
    index = build_document_index(tmp_path, include_reports=False)

    results = search_document_index("zzzz unmatched token", index)

    assert results == []
