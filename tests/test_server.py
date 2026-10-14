from pathlib import Path

import pytest

from spacestd import server

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def demo_docs(monkeypatch):
    monkeypatch.setenv("SPACESTD_DOCS", str(FIXTURES))
    server.get_index.cache_clear()
    yield
    server.get_index.cache_clear()


def test_tools_registered():
    import asyncio

    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert names == {"list_documents", "get_requirement", "search_requirements", "get_references", "get_table",
                     "compare_topic", "get_section_outline"}


def test_get_requirement_found_and_missing():
    hit = server.get_requirement("DEMO-E-ST-99C", "5.1.2a")
    assert hit["found"] and hit["citation"] == "DEMO-E-ST-99C Rev.1, 5.1.2a"
    miss = server.get_requirement("DEMO-E-ST-99C", "7.7.7a")
    assert miss["found"] is False


def test_search_and_references():
    res = server.search_requirements("code coverage category A", limit=3)
    assert res["results"][0]["req_id"] == "5.2.2a" and set(res) == {"results"}
    res = server.search_requirements("What does NASA-STD-7003 require for code coverage?")
    assert res["not_loaded"] == ["NASA-STD-7003"] and res["notes"]
    refs = server.get_references("DEMO NPR 9999.1", "SWE-950")
    assert refs["references"] == ["NASA-HDBK-2203"]


def test_get_table_missing_lists_tables():
    res = server.get_table("DEMO-E-ST-99C", "Table 9-9")
    assert res["found"] is False and res["tables"] == []
    assert server.get_table("DEMO-E-ST-99C", "")["tables"] == []


def test_section_outline():
    whole = server.get_section_outline("DEMO-E-ST-99C")
    assert whole["found"] and [s["clause"] for s in whole["sections"]] == ["5", "5.1", "5.2"]
    assert whole["sections"][0]["records"] == 6 and "records" not in whole
    deep = server.get_section_outline("DEMO-E-ST-99C", depth=3)
    assert "5.1.1" in [s["clause"] for s in deep["sections"]]
    sec = server.get_section_outline("DEMO-E-ST-99C", "5.2")
    assert [(s["clause"], s["title"], s["records"]) for s in sec["sections"]] == [
        ("5.2", "Verification", 3), ("5.2.1", "Unit testing", 2), ("5.2.2", "Code coverage", 1)]
    assert sec["records"] == []
    leaf = server.get_section_outline("DEMO-E-ST-99C", "5.2.1.")
    assert [r["req_id"] for r in leaf["records"]] == ["5.2.1a", "5.2.1b"]
    assert leaf["records"][0]["citation"] == "DEMO-E-ST-99C Rev.1, 5.2.1a" and "text" not in leaf["records"][0]
    assert server.get_section_outline("DEMO-E-ST-99C", "9.9")["found"] is False
    assert server.get_section_outline("NOT-A-DOC")["found"] is False


def test_empty_query_returns_message():
    import asyncio
    import json

    from spacestd import tools
    from spacestd.index import StandardsIndex

    msg = "Empty query"
    for res in (server.search_requirements(""), server.search_requirements("   "),
                tools.search_requirements(StandardsIndex([]), "")):
        assert res["found"] is False and res["message"].startswith(msg) and "list_documents" in res["message"]
    out = asyncio.run(server.mcp.call_tool("search_requirements", {}))
    assert not out.is_error
    structured = json.loads(out.content[0].text)
    assert structured["found"] is False and structured["message"].startswith(msg)
