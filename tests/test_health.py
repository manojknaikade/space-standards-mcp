"""Parse health report (A1, ADR-0006): metrics, thresholds, report and the `checked` tier.

Invented document numbers and text only (ADR-0002).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from spacestd import health
from spacestd.catalogue import build_catalogue
from spacestd.health import Health, judge, measure, name_check, ragged, render, run, valid_id, write_json
from spacestd.index import StandardsIndex
from spacestd.models import Cell, Document, Requirement, Table, TableRow

FIXTURES = Path(__file__).parent / "fixtures"
LETTERS = "abcdefghijkl"
# 24 records: an ECSS standard needs at least THRESHOLDS["min_records"] (20) to be `checked`
GOOD = "4 Requirements\n" + "".join(
    f"4.{n} Invented clause {n}\n" + "".join(f"{c}. The supplier shall do invented thing {n}{c}.\n" for c in LETTERS)
    for n in (1, 2))
# deliberately broken: headings and prose, but no lettered item or tag the parser can turn into a record
BROKEN = "4 Requirements\nInvented prose with no requirement markers at all.\n4.1 General\nMore invented prose.\n"


def _copy_fixtures(dest: Path) -> None:
    for f in FIXTURES.iterdir():
        shutil.copy(f, dest / f.name)


@pytest.mark.parametrize("req_id, family, ok", [
    ("4.3.1a", "ECSS", True),
    ("A.2.1<5.2>b", "ECSS", True),
    ("5.1aa", "ECSS", True),
    ("4.3.1ab", "ECSS", False),
    ("4.3.1a (duplicate 2)", "ECSS", False),
    ("Table 4-3", "ECSS", False),
    ("ABC 24", "NASA", True),
    ("ABC 11 / 7.2.1.a", "NASA", True),
    ("4.1.1 guidance 3", "NASA", True),
    ("ABC 24 (duplicate)", "NASA", False),
    ("4.1.1a", "NASA", True),  # tagless NASA: section + letter (PARSING_NOTES H2)
    ("4.3(1)", "NASA", True),
    ("4.4 req 2", "NASA", True),
    ("AB2 6001", "NASA", True),  # tag prefix ending in a digit
    ("4.3(1) (duplicate)", "NASA", False),
    ("4.3.1ab", "NASA", False),
    ("SWE-901", "other", True),
    ("5.1.1a", "other", True),
    ("orphan", "other", False),
])
def test_valid_id(req_id, family, ok):
    assert valid_id(req_id, family) is ok


def _table(rows):
    return Table("DEMO-X", "", "Table 1", "Invented", ["Part"], ["A", "B"], rows)


def test_ragged_rows():
    full = TableRow({"Part": "one"}, {"A": Cell("1"), "B": Cell("2")})
    assert not ragged(_table([full]))
    assert ragged(_table([full, TableRow({"Part": "two"}, {"A": Cell("1")})]))  # missing column
    assert ragged(_table([TableRow({"Part": ""}, {"A": Cell("1"), "B": Cell("2")})]))  # no label
    assert ragged(_table([TableRow({"Part": "x"}, {"A": Cell("1"), "B": Cell("2"), "C": Cell("3")})]))  # extra


def test_name_check(tmp_path):
    assert name_check("ECSS-E-ST-99-01C_Rev.1.pdf", "ECSS-E-ST-99-01C") == "match"
    assert name_check("ECSS-E-ST-99-01C_Rev.1.pdf", "ECSS-E-ST-99-02C") == "differs"
    # H3: the same standard named in a shorter or different form is not "another standard" (invented numbers)
    assert name_check("NASA-STD-9876 - 2022-07-15-NASA-STD-9876A-Approved.pdf", "NASA-STD-9876A") == "match"
    assert name_check("ECSS-E-ST-99-01 Rev.1(31May2022).pdf", "ECSS-E-ST-99-01C") == "match"
    assert name_check("nasa-std-98761a.pdf", "NASA-STD-9876.1A") == "match"
    assert name_check("NASA-STD-9876Ver-40.pdf", "NASA-STD-9876") == "match"
    assert name_check("ECSS-E-HB-99-01_Part1A.pdf", "ECSS-E-HB-99-01 Part 1A") == "match"
    assert name_check("NASA-STD-9876.2A.pdf", "NASA-STD-9876.1A") == "differs"
    assert name_check("ECSS-E-HB-99-01_Part2A.pdf", "ECSS-E-HB-99-01 Part 1A") == "differs"
    assert name_check("downloaded file.pdf", "ECSS-E-ST-99-02C") == "none"
    (tmp_path / "ECSS-E-ST-99-01C.meta.yaml").write_text("doc_id: ECSS-E-ST-99-02C\nissue: ''\n")
    assert name_check(str(tmp_path / "ECSS-E-ST-99-01C.pdf"), "ECSS-E-ST-99-02C") == "sidecar"


def test_judge_thresholds():
    ok = Health("D", "", "d.txt", "ECSS", "standard", records=20, valid_ids=20, tables=10, ragged_tables=1)
    assert judge(ok) == []
    assert judge(Health("D", "", "d.txt", "ECSS", "standard", records=19, valid_ids=19)) == ["19 records < 20"]
    # handbooks and other types keep the low floor until A5 adds section records
    assert judge(Health("D", "", "d.txt", "ECSS", "handbook", records=7, valid_ids=7)) == []
    assert judge(Health("D", "", "d.txt", "ECSS", "handbook", records=2, valid_ids=2)) == ["2 records < 3"]
    assert judge(Health("D", "", "d.txt", "other", "", records=2, valid_ids=2)) == ["2 records < 3"]
    # one ragged table passes whatever the share; two need the share to stay within 10 %
    assert judge(Health("D", "", "d.txt", "ECSS", "standard", records=20, valid_ids=20, tables=2,
                        ragged_tables=1)) == []
    low = Health("D", "", "d.txt", "ECSS", "standard", records=20, valid_ids=18, unparsed=10, tables=4,
                 ragged_tables=2)
    assert judge(low) == ["valid IDs 90% < 95%", "ragged tables 2/4"]  # ECSS standard: prose is not gated
    nasa = Health("D", "", "d.txt", "NASA", "standard", records=20, valid_ids=20, unparsed=10)
    assert judge(nasa) == ["unparsed 33% > 10%"]
    hb = Health("D", "", "d.txt", "ECSS", "handbook", records=20, valid_ids=20, unparsed=10)
    assert judge(hb) == ["unparsed 33% > 10%"]
    lost = Health("D", "", "d.txt", "ECSS", "standard", records=20, valid_ids=20, body_words=100, covered_words=70)
    assert judge(lost) == ["coverage 70% < 75%"]
    # adoption notices have few or no records by nature: one reason, no thresholds
    assert judge(Health("D", "", "d.txt", "ECSS", "adoption notice", records=0)) == ["adoption notice"]
    named = Health("D", "", "d.txt", "ECSS", "standard", records=20, valid_ids=20, name_id="differs")
    assert judge(named) == ["file name names another standard"]
    assert judge(Health("D", "", "d.txt", "ECSS", "standard", error="ValueError")) == ["parse error (ValueError)"]


def test_coverage_keeps_a_long_document_with_few_records_unchecked():
    """H6: a 400-page handbook with 7 records passed the handbook floor; coverage now catches it."""
    thin = Health("D", "", "d.pdf", "ECSS", "handbook", records=7, valid_ids=7, body_words=40000, covered_words=300)
    assert judge(thin) == ["coverage 1% < 75%"]
    dense = Health("D", "", "d.pdf", "ECSS", "handbook", records=7, valid_ids=7, body_words=400, covered_words=320)
    assert judge(dense) == [] and dense.coverage == 0.8
    # text files are not measured (body_words 0): no coverage reason
    assert judge(Health("D", "", "d.txt", "ECSS", "handbook", records=7, valid_ids=7)) == []


def test_measure_counts_record_and_unparsed_words():
    reqs = [Requirement("D", "", "4.1a", "4.1", "Widgets shall be blue.", notes=["An invented note."])]
    doc = Document("D", "", "", "d.pdf", requirements=reqs, unparsed=["4.1: Invented prose."], body_words=20,
                   unparsed_words=5)
    m = measure(doc, "ECSS")
    assert (m["body_words"], m["covered_words"], m["unparsed"]) == (20, 4 + 3 + 5, 1)


def test_fixtures_are_checked(tmp_path):
    _copy_fixtures(tmp_path)
    results = run(tmp_path)
    assert {h.doc_id: h.tier for h in results} == {
        "DEMO NPR 9999.1": "checked", "DEMO-E-ST-98C": "checked", "DEMO-E-ST-99C": "checked",
        "ECSS-E-HB-99-01A": "checked"}
    ecss = next(h for h in results if h.doc_id == "DEMO-E-ST-99C")
    assert (ecss.records, ecss.valid_ids, ecss.name_id, ecss.error) == (6, 6, "sidecar", "")
    assert ecss.by_kind == {"requirement": 6}


def test_broken_document_is_unchecked(tmp_path):
    (tmp_path / "ECSS-E-ST-99-01C_Rev.1.txt").write_text(GOOD, encoding="utf-8")
    (tmp_path / "ECSS-E-ST-99-02C_Rev.1.txt").write_text(BROKEN, encoding="utf-8")
    by_id = {h.doc_id: h for h in run(tmp_path)}
    assert by_id["ECSS-E-ST-99-01C"].tier == "checked"
    assert by_id["ECSS-E-ST-99-01C"].name_id == "match"
    broken = by_id["ECSS-E-ST-99-02C"]
    assert (broken.tier, broken.records, broken.reasons) == ("unchecked", 0, ["0 records < 20"])


def test_adoption_notice_is_listed_not_judged(tmp_path):
    (tmp_path / "ECSS-E-AS-99-01C.txt").write_text(BROKEN, encoding="utf-8")
    [h] = run(tmp_path)
    assert (h.doc_type, h.tier, h.reasons) == ("adoption notice", "unchecked", ["adoption notice"])
    assert "1 × adoption notice" in render([h], "loaded")


def test_parse_error_is_recorded_without_its_message(tmp_path, monkeypatch):
    (tmp_path / "ECSS-E-ST-99-01C_Rev.1.txt").write_text(GOOD, encoding="utf-8")

    def boom(*a, **k):
        raise ValueError("a message that could quote the document")

    monkeypatch.setattr(health, "load_document", boom)
    [h] = run(tmp_path)
    assert (h.tier, h.error, h.reasons) == ("unchecked", "ValueError", ["parse error (ValueError)"])
    assert "quote" not in render([h], "loaded")


def test_corpus_all_includes_documents_not_loaded(tmp_path):
    (tmp_path / "ECSS-E-ST-99-01C_Rev.1.txt").write_text(GOOD, encoding="utf-8")
    (tmp_path / "bundle").mkdir()
    (tmp_path / "bundle" / "ECSS-E-ST-99-03C.txt").write_text(GOOD, encoding="utf-8")
    assert [h.doc_id for h in run(tmp_path)] == ["ECSS-E-ST-99-01C"]
    assert [h.doc_id for h in run(tmp_path, "all")] == ["ECSS-E-ST-99-01C", "ECSS-E-ST-99-03C"]


def test_health_json_marks_catalogue_and_list_documents(tmp_path, monkeypatch):
    (tmp_path / "ECSS-E-ST-99-01C_Rev.1.txt").write_text(GOOD, encoding="utf-8")
    (tmp_path / "ECSS-E-ST-99-02C_Rev.1.txt").write_text(BROKEN, encoding="utf-8")
    assert {e.tier for e in build_catalogue(tmp_path).entries} == {"unchecked"}
    write_json(tmp_path, run(tmp_path), "loaded")
    cat = build_catalogue(tmp_path)
    assert {e.doc_id: e.tier for e in cat.entries} == {"ECSS-E-ST-99-01C": "checked", "ECSS-E-ST-99-02C": "unchecked"}
    index = StandardsIndex(cat.load_documents(), catalogue=cat)
    assert {d["doc_id"]: d["tier"] for d in index.list_documents()} == {
        "ECSS-E-ST-99-01C": "checked", "ECSS-E-ST-99-02C": "unchecked"}
    # a parser change makes the report stale: back to unchecked until it is re-run
    monkeypatch.setattr(health, "_code_version", lambda: "changed")
    assert {e.tier for e in build_catalogue(tmp_path).entries} == {"unchecked"}


def test_json_keeps_earlier_results_of_the_same_parser(tmp_path):
    (tmp_path / "ECSS-E-ST-99-01C_Rev.1.txt").write_text(GOOD, encoding="utf-8")
    (tmp_path / "bundle").mkdir()
    (tmp_path / "bundle" / "ECSS-E-ST-99-03C.txt").write_text(GOOD, encoding="utf-8")
    write_json(tmp_path, run(tmp_path, "all"), "all")
    path = write_json(tmp_path, run(tmp_path), "loaded")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert [d["doc_id"] for d in data["documents"]] == ["ECSS-E-ST-99-01C", "ECSS-E-ST-99-03C"]
    assert build_catalogue(tmp_path).get("ECSS-E-ST-99-03C").tier == "checked"


def test_report_is_text_free(tmp_path):
    _copy_fixtures(tmp_path)
    md = render(run(tmp_path), "loaded")
    assert "| DEMO-E-ST-99C | Rev.1 | checked | 6 | 6/0/0/0/0 | 100% |" in md
    assert "4 documents: 0 verified, 4 checked, 0 unchecked" in md
    for f in FIXTURES.glob("*.txt"):  # no line of the (invented) source text reaches the report
        for line in f.read_text(encoding="utf-8").splitlines():
            if len(line.split()) > 3:
                assert line not in md


def test_cli_writes_report_and_json(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    _copy_fixtures(docs)
    out = tmp_path / "CORPUS_HEALTH.md"
    monkeypatch.setattr(sys, "argv", ["health", str(docs), "--out", str(out), "--no-cache"])
    health.main()
    assert "# Corpus parse health" in out.read_text(encoding="utf-8")
    assert (docs / ".spacestd-cache" / "health.json").exists()


def test_handbook_section_records_count_toward_coverage(tmp_path):
    # A5: a handbook's prose is covered by its section records, whose clause-number IDs are valid
    _copy_fixtures(tmp_path)
    hb = next(h for h in run(tmp_path) if h.doc_id == "ECSS-E-HB-99-01A")
    assert (hb.records, hb.valid_ids, hb.by_kind, hb.unparsed, hb.tier) == (4, 4, {"guidance": 4}, 0, "checked")


def test_measure_handbook_section_ids_and_coverage():
    reqs = [Requirement("ECSS-E-HB-99A", "", "4.2.1", "4.2.1", "Invented prose of four words.", kind="guidance"),
            Requirement("ECSS-E-HB-99A", "", "A.2", "A.2", "More invented prose.", kind="guidance")]
    doc = Document("ECSS-E-HB-99A", "", "", "d.pdf", requirements=reqs, body_words=10)
    m = measure(doc, "ECSS")
    assert (m["valid_ids"], m["covered_words"], m["unparsed"]) == (2, 8, 0)
    # a bare number is valid only on a guidance record: a requirement still needs its letter
    doc.requirements[0].kind = "requirement"
    assert measure(doc, "ECSS")["valid_ids"] == 1
