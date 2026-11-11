"""Edition dates and the revision guard: a named issue that is not the loaded one is reported, never
answered silently. Invented document numbers and text only (ADR-0002)."""

from __future__ import annotations

import pytest

from spacestd import tools
from spacestd.catalogue import build_catalogue
from spacestd.editions import find_dates, issue_date, issue_differs, issue_words
from spacestd.index import StandardsIndex

TEXT = "4 Requirements\n4.1 General\na. The supplier shall do an invented thing.\n"


@pytest.fixture()
def index(tmp_path):
    (tmp_path / "ECSS-E-ST-99-01C_Rev.2(15October2031).txt").write_text(TEXT, encoding="utf-8")
    (tmp_path / "NASA-STD-9001B.txt").write_text(TEXT, encoding="utf-8")
    cat = build_catalogue(tmp_path)
    return StandardsIndex(cat.load_documents(), catalogue=cat)


@pytest.mark.parametrize("text, iso", [
    ("ECSS-E-ST-99-01C_Rev.2(15October2031)", "2031-10-15"),
    ("NASA-STD-9001 - 2031-06-25_final", "2031-06-25"),
    ("Revalidated: 03/13/2031", "2031-03-13"),
    ("Approved July 4, 2031", "2031-07-04"),
    ("ECSS-E-HB-99-01_Part1A(5Decmber2031)", "2031-12-05"),  # a misspelt month still starts with its 3 letters
])
def test_find_dates(text, iso):
    assert [d.isoformat() for d in find_dates(text)] == [iso]


def test_no_date_in_a_plain_name(tmp_path):
    assert find_dates("NASA-STD-9001B") == []
    assert issue_date(tmp_path / "NASA-STD-9001B.txt") == ""


def test_issue_words_and_differs():
    assert issue_words(" Rev.2 Corr.1, clause 5") == {"rev": "2", "corr": "1"}
    assert issue_words(" w/Change 4") == {"change": "4"}
    assert issue_words(" requires a plan") == {}
    assert issue_differs({"rev": "1"}, "Rev.2") and issue_differs({"rev": "1"}, "")
    assert not issue_differs({"rev": "2"}, "Rev.2 Corr.1")


def test_records_carry_the_issue_date(index):
    rec = tools.get_requirement(index, "ECSS-E-ST-99-01", "4.1a")
    assert rec["found"] and rec["issue"] == "Rev.2" and rec["issue_date"] == "2031-10-15"
    assert tools.get_requirement(index, "ECSS-E-ST-99-01C Rev.2", "4.1a")["found"]  # the loaded issue, named


def test_lookup_of_another_issue_is_refused_with_the_loaded_one(index):
    out = tools.get_requirement(index, "ECSS-E-ST-99-01C Rev.1", "4.1a")
    assert out["found"] is False
    assert out["loaded_issues"] == [{"doc_id": "ECSS-E-ST-99-01C", "issue": "Rev.2", "issue_date": "2031-10-15"}]
    other = tools.get_requirement(index, "NASA-STD-9001A", "4.1a")
    assert other["found"] is False and other["loaded_issues"][0]["doc_id"] == "NASA-STD-9001B"
    assert "loaded_issues" not in tools.get_requirement(index, "NASA-STD-9001B", "9.9z")


def test_search_reports_the_issue_mismatch(index):
    out = tools.search_requirements(index, "What does ECSS-E-ST-99-01C Rev.1 require of the supplier?")
    assert [m["doc_id"] for m in out["issue_mismatch"]] == ["ECSS-E-ST-99-01C"]
    assert out["issue_mismatch"][0]["asked"] == "ECSS-E-ST-99-01C Rev.1"
    assert any("not loaded" in n for n in out["notes"])
    letter = tools.search_requirements(index, "invented thing in NASA-STD-9001A")
    assert letter["issue_mismatch"][0]["reason"] == "another revision letter is loaded"
    assert "issue_mismatch" not in tools.search_requirements(index, "ECSS-E-ST-99-01C Rev.2 invented thing")
    assert "issue_mismatch" not in tools.search_requirements(index, "ECSS-E-ST-99-01 invented thing")


def test_lookup_help(tmp_path):
    """A miss in a loaded document is never a dead end: the clause's records, the parent record of an item,
    the identifier printed at the start of a record, or the nearest IDs."""
    text = ("4 Requirements\n4.1 General\na. The supplier shall do an invented thing.\nb. The supplier shall do another.\n"
            "4.2 Other\na. [XQ&A 7] The supplier shall keep an invented record.\n")
    (tmp_path / "ECSS-E-ST-99-02C.txt").write_text(text, encoding="utf-8")
    cat = build_catalogue(tmp_path)
    idx = StandardsIndex(cat.load_documents(), catalogue=cat)
    clause = tools.get_requirement(idx, "ECSS-E-ST-99-02", "4.1")
    assert clause["found"] is False and [r["req_id"] for r in clause["records_in_clause"]] == ["4.1a", "4.1b"]
    item = tools.get_requirement(idx, "ECSS-E-ST-99-02", "4.1a(2)")
    assert item["found"] and item["req_id"] == "4.1a" and item["asked_for"] == "4.1a(2)" and "4.1a" in item["note"]
    assert tools.get_requirement(idx, "ECSS-E-ST-99-02", "XQ&A 7")["req_id"] == "4.2a"
    near = tools.get_requirement(idx, "ECSS-E-ST-99-02", "4.2z")
    assert near["found"] is False and near["nearest_ids"] == ["4.2a"]
    assert "nearest_ids" not in tools.get_requirement(idx, "ECSS-E-ST-99-02", "9.9.9z")


def test_dates_come_in_the_order_printed():
    """Mixed forms in one name: the last one printed is the edition's date, whatever its form."""
    name = "NASA-STD-9001B_2031-06-25_w-change(4July2031)"
    assert [d.isoformat() for d in find_dates(name)] == ["2031-06-25", "2031-07-04"]
    assert issue_date(name + ".txt") == "2031-07-04"


def test_table_list_of_another_issue_is_refused(index):
    out = tools.get_table(index, "ECSS-E-ST-99-01C Rev.1")
    assert out["found"] is False and out["loaded_issues"][0]["issue"] == "Rev.2"
    assert tools.get_table(index, "ECSS-E-ST-99-01C Rev.2") == tools.get_table(index, "ECSS-E-ST-99-01")
