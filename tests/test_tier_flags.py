"""Tier, page and the "check against the source" flag on tool results, and the citation gate (A3). Invented data."""

from pathlib import Path

import pytest

from spacestd import index as index_mod
from spacestd import tools
from spacestd.catalogue import Catalogue, Entry
from spacestd.citations import CitationChecker
from spacestd.index import StandardsIndex, check_flag
from spacestd.models import Cell, Document, Requirement, Table, TableRow

DOC = "DEMO-STD-7000B"


def make_index(page=12) -> StandardsIndex:
    t = Table(DOC, "", "Table 2", "Invented design factors", ["Material"], ["Ultimate"],
              [TableRow({"Material": "Metallic"}, {"Ultimate": Cell("7,25", 7.25)})], page=page)
    doc = Document(DOC, "", "", "", [
        Requirement(DOC, "", "DSR 3", "4", "Factors per Table 2.", tables=["Table 2"], page=11),
        Requirement(DOC, "", "DSR 4", "5", "Margin of 3 applies.", page=13)], tables=[t])
    return StandardsIndex([doc])


@pytest.fixture
def verified(monkeypatch):
    monkeypatch.setattr(index_mod, "VERIFIED", {(DOC, "")})


def test_records_carry_tier_and_page():
    idx = make_index()
    r = tools.get_requirement(idx, DOC, "DSR 3")
    assert r["tier"] == "unchecked" and r["page"] == 11
    hit = tools.search_requirements(idx, "ultimate metallic factor")["results"][0]
    assert hit["tier"] == "unchecked"
    assert hit["matched_table_row"]["page"] == 12
    assert hit["matched_table_row"]["check"] == "check against the source, page 12"


def test_table_and_rows_flagged_when_below_verified():
    t = tools.get_table(make_index(), DOC, "Table 2")
    assert t["tier"] == "unchecked" and t["check"] == "check against the source, page 12"
    assert t["rows"][0]["tier"] == "unchecked" and t["rows"][0]["page"] == 12
    assert t["rows"][0]["check"] == "check against the source, page 12"
    assert t["rows"][0]["labels"] == {"Material": "Metallic"}  # otherwise unchanged


def test_flag_omits_page_when_unknown():
    t = tools.get_table(make_index(page=None), DOC, "Table 2")
    assert t["check"] == "check against the source" and "page" not in t["rows"][0]
    assert check_flag(None) == "check against the source"


def test_no_flag_on_verified(verified):
    idx = make_index()
    t = tools.get_table(idx, DOC, "Table 2")
    assert t["tier"] == "verified" and "check" not in t and "check" not in t["rows"][0]
    hit = tools.search_requirements(idx, "ultimate metallic factor")["results"][0]
    assert hit["tier"] == "verified" and "check" not in hit["matched_table_row"]
    assert tools.get_requirement(idx, DOC, "DSR 3")["tier"] == "verified"


def test_tier_follows_catalogue_when_issue_matches():
    idx = make_index()
    entry = Entry(DOC, "", "", "other", "", "", "", "x.txt", tier="checked", loaded=True)
    idx.catalogue = Catalogue(Path("."), [entry], None)
    assert tools.get_table(idx, DOC, "Table 2")["tier"] == "checked"
    assert idx.tier_of(DOC, "Rev.9") == "unchecked"
    assert idx.list_documents()[0]["tier"] == "checked"


def test_table_listing_has_tier():
    entry = tools.get_table(make_index(), DOC, "")["tables"][0]
    assert entry["tier"] == "unchecked" and "check" not in entry


# -- citation gate ---------------------------------------------------------------------------------
def test_gate_rejects_table_number_without_flag():
    res = CitationChecker(make_index()).check(f"{DOC} Table 2: ultimate factor 7.25 for metallic parts.")
    assert res.ungrounded == ["7.25"] and res.unflagged == ["7.25"]
    assert res.to_dict()["unflagged"] == ["7.25"]


def test_gate_accepts_flag_in_same_sentence():
    chk = CitationChecker(make_index())
    ans = f"{DOC} Table 2: ultimate factor 7.25 for metallic parts (Check against the source)."
    assert chk.check(ans).ungrounded == []
    assert chk.check(f"{DOC} Table 2 gives 7.25 (page 12).").ungrounded == []
    assert chk.check(f"{DOC} Table 2 gives 7.25 (p. 12).").ungrounded == []


def test_gate_flag_must_be_near_the_number():
    chk = CitationChecker(make_index())
    assert chk.check(f"{DOC} Table 2: factor 7.25. It is metallic. Please check against the source.").ungrounded == ["7.25"]
    assert chk.check(f"{DOC} Table 2: factor 7.25 (page 99).").ungrounded == ["7.25"]  # not the table's page
    assert chk.check(f"{DOC} Table 2:\n- factor 7.25\n- check against the source, page 12").ungrounded == ["7.25"]


def test_gate_through_owning_requirement_needs_flag_too():
    chk = CitationChecker(make_index())
    assert chk.check(f"{DOC} DSR 3: ultimate 7.25.").unflagged == ["7.25"]
    assert chk.check(f"{DOC} DSR 3: ultimate 7.25, check against the source.").ungrounded == []


def test_gate_extra_record_tables_need_flag():
    chk = CitationChecker(make_index())
    assert chk.check("Factor 7.25.", extra_records=[f"{DOC}|Table 2"]).unflagged == ["7.25"]
    assert chk.check("Factor 7.25, page 12.", extra_records=[f"{DOC}|Table 2"]).ungrounded == []


def test_gate_unaffected_for_verified_tables(verified):
    chk = CitationChecker(make_index())
    assert chk.check(f"{DOC} Table 2: ultimate factor 7.25.").ungrounded == []


def test_gate_record_text_numbers_need_no_flag():
    chk = CitationChecker(make_index())
    res = chk.check(f"{DOC} DSR 4: margin of 3 applies.")
    assert res.ungrounded == [] and res.unflagged == []
    # a number in neither stays plainly ungrounded, not "unflagged"
    res = chk.check(f"{DOC} DSR 4: margin of 4.")
    assert res.ungrounded == ["4"] and res.unflagged == []
