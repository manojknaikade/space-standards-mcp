"""Answer checks (citations, numbers, declines) on the invented fixtures (ADR-0002)."""

from pathlib import Path

import pytest

from spacestd.citations import CitationChecker, norm_key
from spacestd.index import StandardsIndex
from spacestd.loaders import load_folder
from spacestd.models import Cell, Document, Requirement, Table, TableRow

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def checker() -> CitationChecker:
    return CitationChecker(StandardsIndex(load_folder(FIXTURES)))


def test_citations_resolved_to_the_named_document(checker):
    ans = ("DEMO-E-ST-99C Rev.1, 5.2.2a requires full statement coverage. "
           "DEMO NPR 9999.1 [SWE-950] also requires unit testing.")
    res = checker.check(ans)
    assert res.cited_keys == {"DEMO-E-ST-99C|5.2.2a", "DEMO NPR 9999.1|SWE-950"}
    assert res.invented == []


def test_unique_id_resolves_without_a_document_name(checker):
    res = checker.check("Clause 4.1.2(b) sets the ultimate factor.")
    assert res.cited_keys == {"DEMO-E-ST-98C|4.1.2b"}


def test_invented_ids_are_flagged(checker):
    res = checker.check("DEMO-E-ST-99C 5.9.9a and SWE-999 say so.")
    assert res.invented == ["5.9.9a", "SWE-999"]
    assert res.cited_keys == set()


def test_ambiguous_id_without_document():
    a = Document("DEMO-A-1C", "", "", "", [Requirement("DEMO-A-1C", "", "4.1a", "4.1", "Text one.")])
    b = Document("DEMO-B-2C", "", "", "", [Requirement("DEMO-B-2C", "", "4.1a", "4.1", "Text two.")])
    res = CitationChecker(StandardsIndex([a, b])).check("See 4.1a.")
    assert res.to_dict()["ambiguous"] == ["4.1a"] and res.invented == []


def test_numbers_grounded_in_cited_records(checker):
    ans = "DEMO-E-ST-98C 4.1.2b: ultimate factor of safety not less than 9.8 for sandwich panels."
    res = checker.check(ans)
    assert res.numbers == ["9.8"] and res.ungrounded == []
    res = checker.check("DEMO-E-ST-98C 4.1.2b: ultimate factor 9.7.")
    assert res.ungrounded == ["9.7"]


def test_numbers_must_come_from_a_cited_record(checker):
    # 9.9 is in 4.1.2a, which this answer does not cite
    res = checker.check("DEMO-E-ST-98C 4.1.2b: yield factor 9.9.")
    assert res.ungrounded == ["9.9"]
    res = checker.check("Yield factor 9.9.", extra_records=["DEMO-E-ST-98C|4.1.2a"])
    assert res.ungrounded == []


def test_ids_names_and_list_markers_are_not_numbers(checker):
    ans = ("1. Per DEMO-E-ST-98C Rev.2 clause 4.1.2 and 4.1.2a (see section 4.2), and DEMOSTR 7, cf. NASA-SP-8007"
           " and ANSI/AIAA S-081:\n(2) nothing else.")
    assert checker.check(ans).numbers == []


def test_table_numbers_ground_through_owning_requirement(monkeypatch):
    monkeypatch.setattr("spacestd.index.VERIFIED", {("DEMO-STD-7000B", "")})  # unflagged table values need a verified tier (A3)
    t =Table("DEMO-STD-7000B", "", "Table 2", "Invented design factors", ["Material"], ["Ultimate"],
              [TableRow({"Material": "Metallic"}, {"Ultimate": Cell("7,25", 7.25)})])
    doc = Document("DEMO-STD-7000B", "", "", "", [
        Requirement("DEMO-STD-7000B", "", "DSR 3", "4", "Factors per Table 2.", tables=["Table 2"])], tables=[t])
    chk = CitationChecker(StandardsIndex([doc]))
    res = chk.check("DEMO-STD-7000B DSR 3: ultimate 7.25 for metallic parts.")
    assert res.ungrounded == [] and res.cited_keys == {"DEMO-STD-7000B|DSR 3"}
    res = chk.check("DEMO-STD-7000B Table 2 gives 7.25.")
    assert res.cited_keys == {"DEMO-STD-7000B|Table 2"} and res.ungrounded == []


def test_declines(checker):
    assert checker.check("The loaded standards do not cover radiation tolerance.").declines
    assert checker.check("This is not covered by the loaded documents.").declines
    for ans in ("The loaded standards don't give a clearance value.", "NASA-STD-5020 isn't one of the loaded standards.",
                "ECSS-E-ST-10-03 isn’t loaded."):
        assert checker.check(ans).declines, ans
    assert not checker.check("DEMO-E-ST-99C 5.2.2a requires 100 % statement coverage.").declines


def test_norm_key():
    assert norm_key("ECSS-E-ST-32-10C|table 4‐3") == norm_key("ECSS-E-ST-32-10C|Table 4-3")
    assert norm_key("demo npr 9999.1|SWE-950") == "DEMO-NPR-9999.1|swe-950"


def test_guidance_records_are_citations():
    doc = Document("DEMO-STD-7000B", "", "", "", [
        Requirement("DEMO-STD-7000B", "", "4.2.1 guidance 3", "4.2.1", "Invented note: use factor 6.5 here.",
                    kind="guidance")])
    res = CitationChecker(StandardsIndex([doc])).check("Use 6.5 (DEMO-STD-7000B, 4.2.1 guidance 3, guidance).")
    assert res.cited_keys == {"DEMO-STD-7000B|4.2.1 guidance 3"}
    assert res.numbers == ["6.5"] and res.ungrounded == [] and res.invented == []
    res = CitationChecker(StandardsIndex([doc])).check("DEMO-STD-7000B 4.2 guidance 9 says so.")
    assert res.invented == ["4.2 guidance 9"] and res.numbers == []


def test_tagless_nasa_ids_are_citations():
    reqs = [Requirement("DEMO-N-2", "", "4.2a", "4.2", "Invented: use factor 1.4."),
            Requirement("DEMO-N-2", "", "4.3(1)", "4.3", "Invented: inspect 3 times."),
            Requirement("DEMO-N-2", "", "4.4 req 1", "4.4", "Invented: weigh every 12 months."),
            Requirement("DEMO-N-2", "", "V7 1234", "4.5", "Invented: log 2 entries.")]
    checker = CitationChecker(StandardsIndex([Document("DEMO-N-2", "", "", "", reqs)]))
    res = checker.check("Use 1.4 (DEMO-N-2 4.2a), inspect 3 times (4.3(1)), weigh every 12 months "
                        "(4.4 req 1) and log 2 entries (V7 1234).")
    assert res.cited_keys == {"DEMO-N-2|4.2a", "DEMO-N-2|4.3(1)", "DEMO-N-2|4.4 req 1", "DEMO-N-2|V7 1234"}
    assert res.invented == [] and res.ungrounded == []
    assert sorted(res.numbers) == ["1.4", "12", "2", "3"]
    res = checker.check("DEMO-N-2 4.3(7) and 4.4 req 9 say so.")
    assert res.invented == ["4.3(7)", "4.4 req 9"]


def test_numbered_item_form_is_not_an_id_without_such_records(checker):
    res = checker.check("DEMO-E-ST-98C equation 4.1(2) gives the margin.")
    assert res.invented == []


def test_ids_of_standards_that_are_not_loaded_are_external(checker):
    for ans in ("Selected per ECSS-Q-ST-70-36 clauses 5.2.1a and 5.9.9a.",
                "Inspect to 50 % of the size in Table 9-1 of ECSS-Q-ST-70-15.",
                "It applies 5.9.9a from ECSS-Q-ST-70-71.",
                "I did not pull the Table 9-1 values in ECSS-Q-ST-70-15."):
        res = checker.check(ans)
        assert res.invented == [] and res.cited_keys == set(), ans
        assert res.to_dict()["external"], ans
    # a loaded document named in between takes over again
    res = checker.check("ECSS-Q-ST-70-36 is not loaded; DEMO-E-ST-99C 5.9.9a says so.")
    assert res.invented == ["5.9.9a"]
    # far from the unloaded name (new sentence), an ID is checked as usual
    res = checker.check("ECSS-Q-ST-70-36 is not loaded. Clause 4.1.2(b) sets the ultimate factor.")
    assert res.cited_keys == {"DEMO-E-ST-98C|4.1.2b"}


def test_nasa_clause_next_to_its_tag_is_not_invented():
    doc = Document("DEMO-N-1", "", "", "", [Requirement("DEMO-N-1", "", "FSR 1", "4.1.2a", "Invented text one."),
                                            Requirement("DEMO-N-1", "", "FSR 2", "4.2b", "Invented text two."),
                                            Requirement("DEMO-N-1", "", "FSR 3", "4.2b", "Invented text three.")])
    checker = CitationChecker(StandardsIndex([doc]))
    res = checker.check("DEMO-N-1 FSR 1 (requirement, 4.1.2a) says so.")
    assert res.invented == [] and res.cited_keys == {"DEMO-N-1|FSR 1"}
    assert checker.index.get("DEMO-N-1", "4.2b") is None  # shared clause: no alias


def test_references_that_are_not_values(checker):
    for ans in ("I did not retrieve Tables 1-7 or Tables 4-3 to 4-6.", "Its joining clause (4.4) is general.",
                "The DRD Q.2.1<5.3> applies, and clause I.2.1<13> too.", "Loaded: DEMO-E-ST-99C, 32-08C, 32C and -32-01.",
                "**4. If the defect recurs**", "It has a buckling section, 4.5."):
        assert checker.answer_numbers(ans) == [], ans
    assert checker.answer_numbers("Use 1.25 (4.4 for joints).") == ["1.25", "4.4"]


def test_clause_numbers_of_cited_records_are_not_values():
    # r12 hand-05: 'Modal (5.7)' headings and 'the checks in 5.4 to 5.7 and 5.8' next to cited 5.7a / 5.8a
    reqs = [Requirement("DEMO-E-ST-1C", "", rid, clause, f"The invented model check {rid} shall pass.")
            for rid, clause in [("5.4.3a", "5.4.3"), ("5.7a", "5.7"), ("5.8a", "5.8")]]
    checker = CitationChecker(StandardsIndex([Document("DEMO-E-ST-1C", "", "", "", reqs)]))
    res = checker.check("DEMO-E-ST-1C: 5.4.3a, 5.7a and 5.8a apply. The reduced-model checks in 5.4 to 5.7 and "
                        "clauses 5.4 to 5.7 and 5.8 matter most.")
    assert res.ungrounded == []
    res = checker.check("DEMO-E-ST-1C, 5.7a: the limit is 5.9 Hz.")  # not a cited clause: still a value
    assert res.ungrounded == ["5.9"]


def test_tag_pair_shorthand_is_two_citations():
    # r12 w1-002: 'PVTR 43/44' was read as one invented ID and the gate declined a correct answer
    tagged = Document("DEMO-STD-9001A", "", "", "", [Requirement("DEMO-STD-9001A", "", f"ZTR {n}", "4.4", f"Text {n}.")
                                                     for n in (43, 44)])
    slashed = Document("DEMO-STD-9002A", "", "", "", [Requirement("DEMO-STD-9002A", "", "FQR 8 / 6.2.1", "6.2.1", "T.")])
    checker = CitationChecker(StandardsIndex([tagged, slashed]))
    res = checker.check("Each axis (DEMO-STD-9001A, ZTR 43/44).")
    assert res.invented == [] and res.cited_keys == {"DEMO-STD-9001A|ZTR 43", "DEMO-STD-9001A|ZTR 44"}
    assert checker.check("DEMO-STD-9002A, FQR 8 / 6.2.1 applies.").cited_keys == {"DEMO-STD-9002A|FQR 8 / 6.2.1"}
    assert checker.check("DEMO-STD-9001A, ZTR 43/47.").invented == ["ZTR 43/47"]  # ZTR 47 does not exist


def test_vehicle_names_are_not_answer_numbers(checker):
    for name in ("Ariane 5", "Ariane-6", "Atlas V", "Delta IV Heavy", "Soyuz-2", "Long March 3B", "H-IIA"):
        assert checker.answer_numbers(f"The {name} example gives 139.5 dB.") == ["139.5"], name
        assert checker.answer_numbers(f"The {name} example.") == [], name
    assert checker.answer_numbers("Ariane 5 fairing, 139.5 dB") == ["139.5"]
    assert checker.answer_numbers("Class 2 parts") == ["2"]
    assert checker.answer_numbers("Type 5 joints") == ["5"]


def test_vehicle_number_does_not_trigger_unflagged_gate():
    t = Table("DEMO-STD-7000B", "", "Table 2", "Invented levels", ["Band"], ["Level"],
              [TableRow({"Band": "250 Hz"}, {"Level": Cell("139,5", 139.5)})], page=9)
    chk = CitationChecker(StandardsIndex([Document("DEMO-STD-7000B", "", "", "", [], tables=[t])]))
    ans = "DEMO-STD-7000B Table 2: the Ariane 5 example gives 139.5 dB (check against the source, page 9)."
    res = chk.check(ans)
    assert res.unflagged == [] and res.ungrounded == []


def test_nasa_paragraph_numbers_after_the_document_name_are_citations():
    reqs = [Requirement("DEMO-N-3A", "", "4.3.1.1", "4.3.1.1", "Invented: keep 7 spare units."),
            Requirement("DEMO-N-3A", "", "4.3.2", "4.3.2", "Invented: log 2 events.")]
    checker = CitationChecker(StandardsIndex([Document("DEMO-N-3A", "", "", "", reqs)]))
    for ans in ("(DEMO-N-3A, 4.3.1.1, requirement)", "(DEMO-N-3A 4.3.1.1)", "(DEMO-N-3A, clause 4.3.1.1)",
                "DEMO-N-3A para. 4.3.1.1 says so", "DEMO-N-3A section 4.3.1.1."):
        res = checker.check(ans)
        assert res.cited_keys == {"DEMO-N-3A|4.3.1.1"} and res.invented == [] and res.numbers == [], ans
    res = checker.check("Keep 7 spare units (DEMO-N-3A, 4.3.1.1) and log 2 events (DEMO-N-3A, 4.3.2).")
    assert res.cited_keys == {"DEMO-N-3A|4.3.1.1", "DEMO-N-3A|4.3.2"} and res.ungrounded == []
    # not a record of that document: a plain section reference, neither cited nor invented
    for ans in ("(DEMO-N-3A, 4.9.9, requirement)", "DEMO-N-3A section 4.9", "DEMO-N-3A 4.3"):
        res = checker.check(ans)
        assert res.cited_keys == set() and res.invented == [] and res.numbers == [], ans


def test_ecss_forms_unchanged_by_paragraph_numbers(checker):
    res = checker.check("DEMO-E-ST-99C, 5.1.2a says so, see DEMO-E-ST-99C 5.1.2.")
    assert res.cited_keys == {"DEMO-E-ST-99C|5.1.2a"} and res.invented == []
