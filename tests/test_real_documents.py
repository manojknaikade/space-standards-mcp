"""Per-document parsing tests on the real standards in documents/ (never committed, ADR-0002).

Skipped when documents/ does not hold the files (e.g. in CI). The assertions carry only
counts, IDs and table values hand-checked against the source PDFs — never standards text.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from spacestd.index import StandardsIndex
from spacestd.loaders import load_folder

DOCS = Path(__file__).resolve().parents[1] / "documents"
EVAL = Path(__file__).resolve().parents[1] / "eval" / "questions.yaml"


@pytest.fixture(scope="module")
def docs():
    if not DOCS.is_dir() or not any(p.suffix.lower() in {".pdf", ".docx", ".doc"} for p in DOCS.iterdir()):
        pytest.skip("real standards not present in documents/")
    return {d.doc_id: d for d in load_folder(DOCS)}


def need(docs, doc_id):
    if doc_id not in docs:
        pytest.skip(f"{doc_id} not in documents/")
    return docs[doc_id]


def ids(doc):
    return [r.req_id for r in doc.requirements]


def vals(table):
    """Value-cell texts per row, in source order (values only, no standards text)."""
    return [[row.cells[c].text for c in table.value_columns] for row in table.rows]


# --------------------------------------------------------------------------- ECSS


def test_ecss_32_10(docs):
    d = need(docs, "ECSS-E-ST-32-10C")
    assert d.issue == "Rev.2 Corr.1"
    assert len(d.requirements) == 28
    # Corr.1 adds the machine IDs Rev.2 lacked (4.3.2.1e, 4.3.2.2b)
    assert all(r.machine_id for r in d.requirements)
    assert {r.req_id: r.machine_id for r in d.requirements}["4.3.2.2b"] == "ECSS-E-ST-32-10_0110035"
    # 35 machine IDs in the PDF: 28 requirements + 6 tables + Figure 4-1
    assert len({t.machine_id for t in d.tables if t.machine_id}) == 6
    assert all(r.kind == "requirement" for r in d.requirements)
    assert [t.table_id for t in d.tables] == [f"Table 4-{i}" for i in range(1, 7)]
    assert {t.table_id: t.clause for t in d.tables}["Table 4-3"] == "4.3.2.1"


def test_ecss_32_01(docs):
    d = need(docs, "ECSS-E-ST-32-01C")
    assert len(d.requirements) == 332
    mids = [r.machine_id for r in d.requirements if r.machine_id]
    assert len(mids) == len(set(mids)) == 331  # 340 machine IDs - tables/figures
    assert len(set(ids(d))) == len(ids(d))
    kinds = {r.kind for r in d.requirements}
    assert {"requirement", "permission", "deleted"} <= kinds
    deleted = [r for r in d.requirements if r.kind == "deleted"]
    assert len(deleted) == 66 and all(r.text.startswith("<<") for r in deleted)
    for rid in ["9a", "9b", "10.2a", "10.5.2.2.1a", "10.7.2.1.3a", "6.3.5.3.1a"]:  # heading edge cases
        assert rid in ids(d)
    # nested list items stay inside their requirement
    assert re.search(r"^1\. ", d.requirements[ids(d).index("6.3.5.3.1a")].text, re.M)


def test_ecss_32(docs):
    d = need(docs, "ECSS-E-ST-32C")
    assert len(d.requirements) == 750
    assert not any(r.machine_id for r in d.requirements)  # 2008 issue: no machine IDs
    assert [r for r in ids(d) if "duplicate" in r] == ["I.2.1<9.1>a (duplicate 2)"]  # letter printed twice in the source
    r = d.requirements[ids(d).index("4.2.5c")]  # launch events listed down to 2.(n)
    assert re.search(r"^\(n\) ", r.text, re.M)
    assert "A.2.1<5.2>a" in ids(d)  # DRD content IDs
    assert not any(r.req_id.startswith(("1", "2", "3")) and r.req_id[1] in ".abcdefgh" for r in d.requirements)


def test_ecss_32_08_word(docs):
    d = need(docs, "ECSS-E-ST-32-08C")
    assert d.source_file.endswith((".docx", ".doc"))
    assert len(d.requirements) == 77
    # IDs from the document's own change log land on existing records
    for rid in ["4.1a", "4.2.11a", "4.6.3b", "4.6.3c", "4.6.4h", "4.6.5e", "4.7b"]:
        assert rid in ids(d)
    assert {r.req_id for r in d.requirements if r.kind == "deleted"} == {"4.4.2a", "4.4.3a"}
    assert any(r.flags for r in d.requirements)  # stale Word cross-references are flagged


# --------------------------------------------------------------------------- NASA


def test_ecss_32_11(docs):
    """B3 hand check (10 Oct 2026): counts, spot-check IDs and table owners against the PDF."""
    d = need(docs, "ECSS-E-ST-32-11C")
    kinds = [r.kind for r in d.requirements]
    assert kinds.count("requirement") == 119 and kinds.count("recommendation") == 9
    assert len(set(ids(d))) == len(ids(d))
    assert ids(d)[0] == "4.1.2a" and ids(d)[-1] == "6.4.2b"
    for rid in ["4.2.3a", "5.2.1a", "5.3.3e", "5.4.2d", "5.7.1.4a", "5.8.2.2b"]:
        assert rid in ids(d)
    owners = {t.table_id: t.clause for t in d.tables}
    assert [t.table_id for t in d.tables] == ["Table 5-1", "Table 5-2", "Table 5-3", "Table 5-4", "Table 6-1"]
    # Tables 5-3 and 5-4 share p. 49 under 5.8.2.2 (round 4: 5-4's caption is no longer skipped as 5-3's wrapped line)
    assert owners == {"Table 5-1": "5.3.2.1", "Table 5-2": "5.8.1.1", "Table 5-3": "5.8.2.2", "Table 5-4": "5.8.2.2",
                      "Table 6-1": "6.2.2"}
    assert [len(t.rows) for t in d.tables] == [3, 3, 6, 3, 4]


def test_ecss_32_03(docs):
    """B3 (10 Oct 2026): 5.4.2b and 5.5g follow display equations and were lost before H14."""
    d = need(docs, "ECSS-E-ST-32-03C")
    kinds = [r.kind for r in d.requirements]
    assert kinds.count("requirement") == 43 and kinds.count("recommendation") == 2
    assert ids(d)[0] == "4.2a" and ids(d)[-1] == "6.2d"
    for rid in ["4.4e", "4.4j", "5.3a", "5.4.2b", "5.4.3b", "5.5c", "5.5f", "5.5g", "5.7a"]:
        assert rid in ids(d)
    assert len(set(ids(d))) == len(ids(d))


def test_nasa_5001b(docs):
    d = need(docs, "NASA-STD-5001B")
    reqs = [r for r in d.requirements if r.kind == "requirement"]
    assert [r.req_id for r in reqs] == [f"FSR {i}" for i in range(1, 62)]
    assert all(r.page <= 26 for r in reqs)  # body only, not the Appendix A matrix
    assert sum(r.kind == "guidance" for r in d.requirements) > 40
    by = {r.req_id: r for r in reqs}
    assert by["FSR 24"].clause == "4.2.1a" and by["FSR 24"].tables == ["Table 1"]
    assert by["FSR 53"].clause == "4.5.2"
    assert [t.table_id for t in d.tables] == [f"Table {i}" for i in range(1, 8)]


def test_nasa_5019a(docs):
    d = need(docs, "NASA-STD-5019A")
    tags = [r.req_id for r in d.requirements if re.fullmatch(r"FCR \d+", r.req_id)]
    assert tags == [f"FCR {i}" for i in range(1, 27)]
    items = [r for r in d.requirements if r.parent]
    assert len(items) > 150 and all(r.req_id.startswith(r.parent + " / ") for r in items)
    by = {r.req_id: r for r in d.requirements}
    assert "FCR 11 / 7.2.1.k" in by and "FCR 11 / 7.2.2.m" in by
    assert re.search(r"^e\. ", by["FCR 9"].text, re.M)  # list continues after a guidance paragraph
    assert by["FCR 6"].notes and by["FCR 6"].notes[0].startswith("Rationale")
    assert d.unparsed == []
    # third-level 'A.'/'B.' and 'i.'/'ii.' items stay with their '(n)' item (hand test F1)
    c = by["FCR 12 / 7.3.2.c"].text
    assert re.search(r"^\(2\) .*\nA\. .*\nB\. .*1\.4", c, re.M | re.S)
    fb = by["FCR 7 / 6.1.1.4.b"].text
    assert [m for m in re.findall(r"^\((\d)\)", fb, re.M)] == list("1234567")
    assert len(re.findall(r"^[AB]\. ", fb, re.M)) == 6 and re.search(r"^ii\. ", fb, re.M)
    for rid in ("FCR 7 / 6.1.1.4", "FCR 11 / 7.2.1", "FCR 11 / 7.2.2", "FCR 11 / 7.2.6"):  # lead-ins only
        assert not re.search(r"^(?:[A-H]|i{1,3})\. |^\(\d\)", by[rid].text, re.M), rid
    assert not re.search(r"^\(\d\)", by["6.1.1.4 guidance 6"].text, re.M)  # list items left the guidance


def test_eval_expected_ids_resolve(docs):
    index = StandardsIndex(list(docs.values()))
    for q in yaml.safe_load(EVAL.read_text(encoding="utf-8")):
        for e in q.get("expected_ids") or []:
            doc_id, rid = e.split("|")
            if doc_id in docs:
                assert index.get(doc_id, rid) is not None, (q["id"], e)


# --------------------------------------------------------------------------- tables (values hand-checked)


def table(docs, doc_id, tid):
    t = next((t for t in need(docs, doc_id).tables if t.table_id == tid), None)
    assert t is not None, tid
    return t


def test_32_10_table_4_2_test_factors(docs):
    t = table(docs, "ECSS-E-ST-32-10C", "Table 4-2")
    assert (len(t.label_columns), len(t.value_columns), len(t.rows)) == (2, 3, 13)
    v = [row[:2] for row in vals(t)]  # KQ, KA
    assert v[0] == ["1,25 a", "1"]  # global flight loads, satellite
    assert v[2:4] == [["1,4", "1,2"], ["1,5", "1,2"]]  # man-rated launch / on orbit; KA in a merged cell
    assert [t.rows[i].cells[t.value_columns[1]].spans_rows for i in (2, 3)] == [True, True]
    assert v[5:8] == [["1,25 a, e", "1"], ["1,25 e", "N/A"], ["2", "N/A"]]
    assert v[9:11] == [["2", "N/A"], ["1,4", "N/A"]]  # storage: two stacked values, one merged N/A
    assert v[11:] == [["1", "1"], ["1", "1"]]
    assert t.rows[0].cells[t.value_columns[0]].footnotes == ["a"]
    assert set(t.footnotes) == set("abcdefghi")


def test_32_10_table_4_3_metallic_and_frp(docs):
    t = table(docs, "ECSS-E-ST-32-10C", "Table 4-3")
    assert (len(t.label_columns), len(t.value_columns), len(t.rows)) == (2, 4, 17)
    v = vals(t)  # FOSY, FOSU, FOSY analysis only, FOSU analysis only
    assert v[0] == ["1,1", "1,25", "1,25", "2,0"]  # metallic, satellite
    assert v[1] == ["1,1", "1,25", "See Note c", "2,0"]  # metallic, launch vehicle
    lv = t.rows[1]
    assert [lv.cells[c].value for c in t.value_columns[:2]] == [1.1, 1.25]
    assert v[2] == ["1,25", "1,4", "1,25 d", "2,0"]  # metallic, man-rated launch
    assert v[3] == ["1,1", "1,5", "1,25 d", "2,0 d"]  # metallic, man-rated on orbit (merged FOSY-analysis cell)
    assert t.rows[3].cells[t.value_columns[2]].spans_rows
    assert v[5] == ["N/A", "1,25", "N/A", "2,0"]  # FRP away from discontinuities, launch vehicle
    assert v[9] == ["N/A", "1,25", "N/A", "2,0"]  # FRP discontinuities, launch vehicle
    assert v[14] == ["N/A", "2,5", "N/A", "5,0"]  # glass/ceramic, satellite
    assert v[16] == ["N/A", "3,0", "N/A", "5,0 e"]


def test_32_10_table_4_4_merged_sub_rows(docs):
    """Three sub-rows per vehicle (failure / gapping-sliding safety critical / other) with merged cells.

    The structure-type cell lists the three sub-rows once; every vehicle band repeats them
    (checked against the rendered page). Rev.2 printed '1,4' three times in the man-rated failure
    FOSU cell (the parser keeps such a stack as one row); Corr.1 prints it once.
    """
    t = table(docs, "ECSS-E-ST-32-10C", "Table 4-4")
    v = vals(t)
    assert len(v) == 11
    assert v[0:3] == [["1,1", "1,25", "1,25", "2,0"], ["N/A", "N/A", "N/A", "N/A"], ["1,1", "1,1", "2,0", "2,0"]]  # satellite
    assert v[3:6] == [["1,1", "1,25", "N/A", "N/A"], ["N/A", "N/A", "2,0", "2,0"], ["1,1", "1,1", "2,0", "2,0"]]  # launch vehicle
    assert v[6] == ["See Note c", "1,4", "See Note c", "See Note c"]  # man-rated, failure
    assert v[7:9] == [["1,4", "1,4", "2,0", "2,0"], ["1,25", "1,25", "2,0", "2,0"]]
    assert [row[1] for row in v[9:]] == ["2,0", "2,0"]  # elastomer
    kinds = [t.rows[i].labels[t.label_columns[0]] for i in range(9)]
    assert [k.split(" - ", 1)[1].split(" (")[0] for k in kinds] == ["Failure", "Gapping/Sliding", "Gapping/Sliding"] * 3
    assert ["(Safety Critical)" in k for k in kinds[:3]] == [False, True, False]
    assert len({t.rows[i].labels[t.label_columns[1]] for i in range(3)}) == 1  # one vehicle label per band


def test_32_10_table_4_2_subscript_spaced(docs):
    t = table(docs, "ECSS-E-ST-32-10C", "Table 4-2")
    kq, ka = (t.rows[1].cells[c] for c in t.value_columns[:2])  # global flight loads, launch vehicle
    assert (kq.text, kq.value, kq.footnotes) == ("1,25 corrected b", 1.25, ["b"])
    assert ka.text == "1 or Jp c"  # one-letter subscript stays attached


def test_q70_table_5_1_bimetallic_matrix(docs):
    """Caption without separator, rotated column headers, triangular matrix, 'Key:' legend."""
    t = table(docs, "ECSS-Q-ST-70C", "Table 5-1")
    assert t.caption.startswith("Compatible couples")
    assert len(t.label_columns) == 1 and len(t.value_columns) == 18 and len(t.rows) == 18
    assert t.value_columns[0] == "Aluminium-Copper alloys" and t.value_columns[-1] == "Zinc, Beryllium"
    assert [r.labels[t.label_columns[0]] for r in t.rows][-1] == "Zinc Beryllium"
    codes = [[c.text for c in r.cells.values()] for r in t.rows]
    assert codes[0] == [""] + "1 1 3 3 3 3 3 3 2 2 3 1 2 2 3 2 2".split()  # first row, diagonal blank
    assert codes[10][11:] == "2 2 1 0 2 1 3".split()  # the row split by diagonal grid lines
    assert all(len([x for x in row if x]) == 17 - n for n, row in enumerate(codes))  # upper triangle
    assert set(t.footnotes) == {"Key 0", "Key 1", "Key 2", "Key 3"}
    assert set(table(docs, "ECSS-Q-ST-70C", "Table 4-1").footnotes) == {"NOTE 1", "NOTE 2", "NOTE 3"}
    assert len(table(docs, "ECSS-Q-ST-70C", "Table 4-1").rows) == 6  # the NOTE block is no row


def test_32_10_tables_4_5_and_4_6(docs):
    t = table(docs, "ECSS-E-ST-32-10C", "Table 4-5")
    assert vals(t) == [
        ["See Note a", "1,25", "See Note a", "2,0"],
        ["N/A", "1,25", "See Note a", "2,0"],  # launch vehicle, global
        ["1,1", "1,25", "See Note a", "2,0"],  # launch vehicle, local
        ["See Note a", "1,4", "See Note a", "N/A"],
    ]
    t = table(docs, "ECSS-E-ST-32-10C", "Table 4-6")
    assert [r[:2] for r in vals(t)] == [["1,1", "1,25"], ["1,1", "1,25"], ["1,25", "1,4"]]


def test_5001b_tables(docs):
    t1 = table(docs, "NASA-STD-5001B", "Table 1")  # ultimate, yield, qualification, proof
    assert vals(t1) == [["1.4", "1.0*", "1.4", "N/A or 1.05**"], ["1.4", "1.25", "1.2", "N/A or 1.05**"]]
    assert t1.rows[1].cells[t1.value_columns[1]].value == 1.25  # protoflight yield
    assert set(t1.footnotes) == {"*", "**"} and t1.clause == "FSR 24"
    t2 = table(docs, "NASA-STD-5001B", "Table 2")
    assert vals(t2) == [["2.0*", "1.4", "1.05"], ["1.4", "1.4", "1.05"], ["2.0*", "1.2", "1.2"], ["1.5", "1.2", "1.2"]]
    assert len({r.labels[t2.label_columns[0]] for r in t2.rows[:2]}) == 1  # merged approach cell
    assert "1.4" in t2.footnotes["*"] and "1.5" in t2.footnotes["*"]
    assert vals(table(docs, "NASA-STD-5001B", "Table 3")) == [["3.0", "1.2"], ["3.0", "2.0"], ["5.0", "N/A"]]
    assert vals(table(docs, "NASA-STD-5001B", "Table 4")) == [["1.5", "1.2"], ["3.0", "2.0"]]
    assert vals(table(docs, "NASA-STD-5001B", "Table 5")) == [["1.65", "2.0", "1.5"], ["N/A", "1.5", "N/A"], ["N/A", "2.0", "N/A"]]
    assert vals(table(docs, "NASA-STD-5001B", "Table 6")) == [["4.0", "4.0", "1.2"], ["2.0", "2.0", "1.2"]]
    t7 = table(docs, "NASA-STD-5001B", "Table 7")
    assert t7.label_columns == [] and vals(t7) == [["1.4", "1.6", "1.2"]]


# --------------------------------------------------------------------------- B3 wave 1 (10 Oct 2026)


def reqs(doc):
    return [r for r in doc.requirements if r.kind == "requirement"]


@pytest.mark.parametrize("doc_id, tag, n, spot", [
    ("NASA-SPEC-5022", "NCPR", 79, [1, 11, 23, 34, 45, 56, 68, 79]),
    ("NASA-STD-5006A", "GWR", 138, [5, 24, 44, 63, 83, 102, 103, 123, 142]),
    ("NASA-STD-5023", "VDVR", 105, [1, 16, 31, 46, 60, 75, 90, 105]),
])
def test_nasa_tagged_counts(docs, doc_id, tag, n, spot):
    d = need(docs, doc_id)
    assert len(reqs(d)) == n
    assert all(re.fullmatch(rf"{tag} \d+", r.req_id) for r in reqs(d))  # no false 'TAG n / section' records (H12)
    for k in spot:
        assert f"{tag} {k}" in ids(d)


def test_nasa_5002b(docs):
    d = need(docs, "NASA-STD-5002B")
    assert len(reqs(d)) == 67  # LAR 68 is printed only in the Appendix A matrix
    assert [r.kind for r in d.requirements if r.req_id == "LAR 7"] == ["deleted"]
    assert "LAR 68" not in ids(d) and all(re.fullmatch(r"LAR \d+", r.req_id) for r in reqs(d))
    for k in [1, 11, 20, 30, 40, 50, 59, 69]:
        assert f"LAR {k}" in ids(d)


def test_nasa_5005d_headings(docs):
    d = need(docs, "NASA-STD-5005D")
    assert len(reqs(d)) == 251
    assert not any("duplicate" in i for i in ids(d))  # italic headings found (H13c)
    for rid in ["4.1a", "4.6.2.1b", "5.2.8b", "5.4.9.1 req 1", "6 req 1", "6.3.1.3.2a", "6.4.4c", "6.4.14a", "6.4.16c"]:
        assert rid in ids(d)


def test_nasa_5018(docs):
    d = need(docs, "NASA-STD-5018")
    assert len(reqs(d)) == 234
    assert not any("duplicate" in i for i in ids(d))  # 4.7.3 heading split from its title (H13c)
    for rid in ["4.2a", "4.5.4 req 1", "4.7.3a", "4.7.3b", "4.7.12b", "4.10.1 req 1", "5.3.6a", "5.7.4f", "5.8.6b",
                "5.12 req 1"]:
        assert rid in ids(d)
    assert [(t.table_id, len(t.rows), len(t.value_columns)) for t in d.tables] == [("Table 1", 4, 2)]


def test_5023_tables_with_caption_on_the_previous_page(docs):
    d = need(docs, "NASA-STD-5023")
    t = {t.table_id: t for t in d.tables}
    assert (t["Table 1"].page, t["Table 3"].page) == (19, 44)  # captions at the foot of pp. 18 / 43 (H16)
    assert vals(t["Table 1"]) == [["3.00", "1.50", "1.25"], ["See Note 1"] * 3, ["2.00", "1.25", "1.10"],
                                  ["1.00", "1.00", "1.00"]]
    assert [row[2] for row in vals(t["Table 3"])] == ["2760 MPa (400 ksi)", "2960 MPa (430 ksi)", "2960 MPa (430 ksi)",
                                                      "4070 MPa (590 ksi)"]


# --------------------------------------------------------------------------- B3 round 4 (11 Oct 2026)


def tbl(docs, doc_id, table_id):
    return {t.table_id: t for t in need(docs, doc_id).tables}[table_id]


def test_ecss_32_02(docs):
    """Two 'can' items (4.5.1.4c, 5.3.1a) are not requirements: 384. Tables 4-5 / 4-8 after H17 (round 4)."""
    d = need(docs, "ECSS-E-ST-32-02C")
    assert len(reqs(d)) == 384 and ids(d)[0] == "4.2.1a" and reqs(d)[-1].req_id == "5.7.2e"
    for rid in ["4.2.1a", "4.3.3.1d", "4.4.2.1f", "4.4.4.3b", "4.5.3.2h", "4.6.2.2m", "5.3.3d", "5.7.2e"]:
        assert rid in ids(d)
    assert [len(t.rows) for t in d.tables] == [2, 2, 2, 2, 4, 2, 2, 6, 2, 2]
    t45 = tbl(docs, "ECSS-E-ST-32-02C", "Table 4-5")  # NOTES block -> footnotes; shaded FOSY is a value column
    assert len(t45.label_columns) == 2 and len(t45.value_columns) == 4 and len(t45.footnotes) == 3
    assert [[r[1], r[3]] for r in vals(t45)[:3]] == [["1,5", "4,0"], ["1,5", "2,5"], ["1,5", "2,5"]]
    t48 = tbl(docs, "ECSS-E-ST-32-02C", "Table 4-8")  # one application name per sub-row
    assert [[r[1], r[3]] for r in vals(t48)[:4]] == [["1,25", "1,5"], ["1,5", "2,5"], ["1,1", "1,5"], ["1,5", "2,5"]]
    assert len({row.labels[t48.label_columns[1]] for row in t48.rows[:4]}) == 4


def test_ecss_33_01(docs):
    d = need(docs, "ECSS-E-ST-33-01C")
    assert len(reqs(d)) == 406 and len(set(ids(d))) == len(ids(d))
    assert [len(t.rows) for t in d.tables] == [2, 7, 7, 7, 9, 7, 7]
    # Tables 4-6 / 4-7: two calculation columns under one header (H17, round 4)
    assert vals(tbl(docs, "ECSS-E-ST-33-01C", "Table 4-6"))[-2:] == [["8260", "6100"], ["8260", "8260"]]
    assert vals(tbl(docs, "ECSS-E-ST-33-01C", "Table 4-7"))[-2:] == [["8260", "12200"], ["12200", "12200"]]


@pytest.mark.parametrize("doc_id, tag, n, spot", [
    ("NASA-STD-5008B", "PCR", 319, [15, 60, 105, 150, 195, 240, 285, 333]),
    ("NASA-STD-5009C", "NER", 74, [1, 12, 22, 33, 43, 54, 64, 74]),
    ("NASA-STD-5012C", "PSER", 28, [1, 5, 9, 13, 17, 21, 25, 28]),
    ("NASA-STD-5017B", "DDMR", 90, [1, 14, 27, 39, 46, 52, 64, 77, 90]),
    ("NASA-STD-7001C", "PVTR", 64, [1, 8, 10, 19, 28, 37, 46, 55, 64]),
])
def test_nasa_tagged_counts_round4(docs, doc_id, tag, n, spot):
    test_nasa_tagged_counts(docs, doc_id, tag, n, spot)


def test_nasa_5008b_table_1(docs):
    t = tbl(docs, "NASA-STD-5008B", "Table 1")  # group headings -> 'Group' column; notes 1-2 -> footnotes
    assert t.label_columns[0] == "Group" and len(t.rows) == 10 and sorted(t.footnotes) == ["1", "2"]
    assert len({row.labels["Group"] for row in t.rows}) == 6


def test_nasa_5009c_tables(docs):
    for tid, first in [("Table 1", [["t", "1.27"], ["0.51", "2.54"], ["1.27", "1.27"]]),
                       ("Table 2", [["t", "0.050"], ["0.020", "0.100"], ["0.050", "0.050"]])]:
        t = tbl(docs, "NASA-STD-5009C", tid)  # stacked sub-rows split, method groups, Symbol-font <= / >= mapped
        assert t.label_columns[0] == "Group" and len(t.rows) == 22 and len({r.labels["Group"] for r in t.rows}) == 5
        assert [r[2:] for r in vals(t)[:3]] == first
        assert not any(0xF000 <= ord(ch) <= 0xF0FF for r in vals(t) for c in r for ch in c)


def test_nasa_5012c_table_1(docs):
    t = tbl(docs, "NASA-STD-5012C", "Table 1")  # footnote superscripts no longer fused into the factors (H17)
    fos = [r[1] for r in vals(t) if re.fullmatch(r"\d\.\d+", r[1])]
    assert fos == ["1.10", "1.40", "1.40", "1.50", "2.0", "1.10", "1.40", "1.20", "1.40", "1.40", "2.00", "2.00",
                   "1.70", "1.50", "2.00"]


def test_nasa_5017b_tables(docs):
    t1 = tbl(docs, "NASA-STD-5017B", "Table 1")
    assert vals(t1) == [["3.00", "1.50", "1.25"]] + [["2.50", "1.35", "1.15"]] * 4 + [["2.00", "1.25", "1.10"],
                                                                                    ["1.00", "1.00", "1.00"]]
    for tid, ncols in [("Table 5", 12), ("Table 7", 8)]:  # rotated headers read as words; legend -> footnotes
        t = tbl(docs, "NASA-STD-5017B", tid)
        assert len(t.value_columns) == ncols and len(t.rows) == 1 and sorted(t.footnotes) == ["Key AN", "Key R"]
        assert not any(re.search(r"(?:\b\w ){4}", name) for name in t.value_columns)


def test_nasa_7001c_table_2_boxed(docs):
    t = tbl(docs, "NASA-STD-7001C", "Table 2")  # a box without inner rules (H16)
    assert (t.page, len(t.rows), t.value_columns) == (18, 6, ["Entry"])


def test_nasa_7003a_paragraph_ids(docs):
    d = need(docs, "NASA-STD-7003A")
    assert [r.req_id for r in reqs(d)] == [
        "4.1.1", "4.1.2", "4.1.2.1", "4.1.2.2", "4.2.1", "4.2.2", "4.3.1", "4.3.1.1", "4.3.2", "4.3.3", "4.3.4",
        "4.3.5", "4.3.6", "4.3.7", "4.4.1", "4.4.2", "4.4.3", "4.4.3.1", "4.4.4", "4.4.4.1", "4.4.5", "4.6.1",
        "4.8.1", "4.8.1.1", "4.8.1.2", "4.8.1.3"]


# --------------------------------------------------------------------------- B3 round 5 (12 Oct 2026)


def test_ecss_10_03_tables(docs):
    """All 14 tables with their continuation pages (group rows in column 0, row-number columns, rows carried
    over a page break, key blocks under the matrices; H18, round 5)."""
    d = need(docs, "ECSS-E-ST-10-03C")
    assert len(reqs(d)) == 431 and reqs(d)[0].req_id == "4.1a" and reqs(d)[-1].req_id == "C.2.1<14>c"
    t = {x.table_id: x for x in d.tables}
    assert [len(x.rows) for x in d.tables] == [35, 18, 28, 20, 28, 11, 28, 16, 34, 17, 34, 17, 34, 17]
    for x in d.tables:  # one row shape per table (no ragged continuation pages)
        assert len({(tuple(r.labels), tuple(r.cells)) for r in x.rows}) == 1, x.table_id
    for tid in ["Table 5-2", "Table 5-4", "Table 5-6", "Table 6-2", "Table 6-4", "Table 6-6"]:
        assert t[tid].label_columns == ["No", "Test"] and len(t[tid].value_columns) == 4
        assert [r.labels["No"] for r in t[tid].rows] == [str(k) for k in range(1, len(t[tid].rows) + 1)]
    for tid in ["Table 5-1", "Table 5-3", "Table 5-5"]:  # equipment-type key a..l and the R / X legend
        assert t[tid].label_columns == ["Group", "Test"] and len(t[tid].value_columns) == 15
        assert set("abcdefghijkl") <= set(t[tid].footnotes)
    for tid in ["Table 6-1", "Table 6-3", "Table 6-5"]:
        assert t[tid].label_columns == ["Group", "Test"] and len({r.labels["Group"] for r in t[tid].rows}) == 7
    assert sorted({r.page for r in t["Table 4-1"].rows if r.page}) == [33]  # p. 33 no longer lost (H15)
    assert vals(t["Table 4-1"])[11:13] == [["20 Hz - 1000 Hz", "-1 dB / +3 dB"], ["1000 Hz - 2000 Hz", "± 3 dB"]]
    assert vals(t["Table 4-2"])[9] == ["> 1,3 hPa", "± 15 %"]


def test_nasa_5020b_tables(docs):
    d = need(docs, "NASA-STD-5020B")
    assert len(reqs(d)) == 32 and reqs(d)[0].req_id == "TFSR 1" and reqs(d)[-1].req_id == "TFSR 32"
    # Table 8 (an Appendix worked example in a box without inner rules) is dropped, not garbled (H19)
    assert [(x.table_id, len(x.rows)) for x in d.tables] == [
        ("Table 1", 3), ("Table 2", 4), ("Table 3", 3), ("Table 4", 3), ("Table 5", 40), ("Table 6", 3), ("Table 7", 11)]
    assert vals(tbl(docs, "NASA-STD-5020B", "Table 7"))[:2] == [["4752", "259", "5011", "20045"],
                                                               ["13038", "651", "13689", "54756"]]


def test_nasa_7002b_table_1_shading(docs):
    d = need(docs, "NASA-STD-7002B")
    assert len(reqs(d)) == 63 and reqs(d)[0].req_id == "PTR 1" and reqs(d)[-1].req_id == "PTR 63"
    t = tbl(docs, "NASA-STD-7002B", "Table 1")  # required tests are marked only by grey fill (H19)
    assert len(t.rows) == 27 and sorted(t.footnotes) == ["1", "2", "3", "4", "5", "6", ">", "shaded"]
    assert sum(c.shaded for r in t.rows for c in r.cells.values()) == 52
    assert [(c.text, c.shaded, c.footnotes) for c in t.rows[0].cells.values()] == [("1", True, ["1"])] * 3
    assert len({r.labels["Group"] for r in t.rows}) == 4  # section bars as groups (one cut into three cells)
    # R6: the first bar is a group too, not the name of the label column
    assert t.label_columns == ["Group", "col0"] and all(r.labels["Group"] for r in t.rows)


def test_r6_parser_quirks(docs):
    # 7003A 4.3: the lead-in paragraph pointing at Table 1 is a guidance record (later 4.3 guidance IDs shift by one)
    d = need(docs, "NASA-STD-7003A")
    by = {r.req_id: r for r in d.requirements}
    assert len(d.requirements) == 69
    assert by["4.3 guidance 1"].kind == "guidance" and by["4.3 guidance 1"].tables == ["Table 1"]
    assert by["4.3 guidance 1"].page == 20 and "4.3 guidance 3" in by
    # 10-03C Table 4-1: '1. ...' is a group row now (36 -> 35 rows); the first rows sit under it
    t = tbl(docs, "ECSS-E-ST-10-03C", "Table 4-1")
    assert len(t.rows) == 35 and t.rows[0].labels["Group"].startswith("1. ")
    assert t.rows[0].labels == t.rows[1].labels and t.rows[2].labels["Group"].startswith("2. ")


def test_every_table_is_searchable(docs):
    """Round 5: tables no record points to get a table-level owner; lowercase 'table 1' references count."""
    from spacestd.index import StandardsIndex
    idx = StandardsIndex(list(docs.values()))
    assert all(idx._table_owners(d, t) for d in docs.values() for t in d.tables)
    pointing = {d.doc_id: [r.req_id for r in d.requirements if "Table 1" in r.tables] for d in docs.values()}
    if "NASA-STD-5008B" in docs:
        assert "PCR 277" in pointing["NASA-STD-5008B"]
    if "NASA-STD-5018" in docs:
        assert "4.5.1 req 1" in pointing["NASA-STD-5018"]
    if "NASA-STD-7003A" in docs:
        hits = idx.search_hits("pyroshock qualification protoflight acceptance margin", doc_id="NASA-STD-7003A", limit=10)
        assert any(h.table is not None and h.table.table_id == "Table 1" for h in hits)


# table IDs and row counts of every verified document (round 5: a rule meant for one table dropped ten
# requirements-matrix tables; this catches a lost or re-shaped table in any verified document)
VERIFIED_TABLES = {
    "ECSS-E-ST-10-03C": {"Table 4-1": 35, "Table 4-2": 18, "Table 5-1": 28, "Table 5-2": 20, "Table 5-3": 28,
        "Table 5-4": 11, "Table 5-5": 28, "Table 5-6": 16, "Table 6-1": 34, "Table 6-2": 17, "Table 6-3": 34,
        "Table 6-4": 17, "Table 6-5": 34, "Table 6-6": 17},
    "ECSS-E-ST-32-01C": {"Table 8-1": 4},
    "ECSS-E-ST-32-02C": {"Table 4-1": 2, "Table 4-2": 2, "Table 4-3": 2, "Table 4-4": 2, "Table 4-5": 4,
        "Table 4-6": 2, "Table 4-7": 2, "Table 4-8": 6, "Table 4-9": 2, "Table 4-10": 2},
    "ECSS-E-ST-32-03C": {},
    "ECSS-E-ST-32-08C": {},
    "ECSS-E-ST-32-10C": {"Table 4-1": 3, "Table 4-2": 13, "Table 4-3": 17, "Table 4-4": 11, "Table 4-5": 4,
        "Table 4-6": 3},
    "ECSS-E-ST-32-11C": {"Table 5-1": 3, "Table 5-2": 3, "Table 5-3": 6, "Table 5-4": 3, "Table 6-1": 4},
    "ECSS-E-ST-32C": {},
    "ECSS-E-ST-33-01C": {"Table 4-1": 2, "Table 4-2": 7, "Table 4-3": 7, "Table 4-4": 7, "Table 4-5": 9,
        "Table 4-6": 7, "Table 4-7": 7},
    "ECSS-Q-ST-70C": {"Table 4-1": 6, "Table 5-1": 18},
    "NASA-SPEC-5022": {},
    "NASA-STD-5001B": {"Table 1": 2, "Table 2": 4, "Table 3": 3, "Table 4": 2, "Table 5": 3, "Table 6": 2,
        "Table 7": 1},
    "NASA-STD-5002B": {"Table 1": 5},
    "NASA-STD-5005D": {},
    "NASA-STD-5006A": {},
    "NASA-STD-5008B": {"Table 1": 10},
    "NASA-STD-5009C": {"Table 1": 22, "Table 2": 22, "Table 3": 1},
    "NASA-STD-5012C": {"Table 1": 20, "Table 2": 29},
    "NASA-STD-5017B": {"Table 1": 7, "Table 2": 2, "Table 3": 4, "Table 4": 2, "Table 5": 1, "Table 6": 14,
        "Table 7": 1, "Table 8": 12},
    "NASA-STD-5018": {"Table 1": 4},
    "NASA-STD-5019A": {"Table 1": 26, "Table 2": 5, "Table 3": 1, "Table 4": 3, "Table 5": 5, "Table 6": 8,
        "Table 7": 3, "Table 8": 1},
    "NASA-STD-5020B": {"Table 1": 3, "Table 2": 4, "Table 3": 3, "Table 4": 3, "Table 5": 40, "Table 6": 3,
        "Table 7": 11},
    "NASA-STD-5023": {"Table 1": 4, "Table 2": 1, "Table 3": 4, "Table 4": 8},
    "NASA-STD-7001C": {"Table 1": 12, "Table 2": 6, "Table 3": 64},
    "NASA-STD-7002B": {"Table 1": 27, "Table 2": 2, "Table 3": 2},
    "NASA-STD-7003A": {"Table 1": 2, "Table 2": 1},
}


@pytest.mark.parametrize("doc_id", sorted(VERIFIED_TABLES))
def test_verified_tables_unchanged(docs, doc_id):
    d = need(docs, doc_id)
    assert {t.table_id: len(t.rows) for t in d.tables} == VERIFIED_TABLES[doc_id]
