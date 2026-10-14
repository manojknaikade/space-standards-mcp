"""Catalogue: recursive discovery, one source per document, corpus.yaml selection (ADR-0006).

Invented document numbers and text only (ADR-0002).
"""

from __future__ import annotations

import json

import docx
import pytest
from test_meta import _write_pdf

from spacestd import tools
from spacestd.catalogue import build_catalogue, classify
from spacestd.index import StandardsIndex
from spacestd.loaders import load_folder, meta_from_text

TEXT = "4 Requirements\n4.1 General\na. The supplier shall do an invented thing.\n"


def _txt(path, text=TEXT):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.mark.parametrize("stem, expected", [
    ("ECSS-E-HB-99-20_Part1A(20March2031)", ("ECSS-E-HB-99-20 Part 1A", "")),
    ("ECSS-E-HB-99-01_Part10A(5December2031)", ("ECSS-E-HB-99-01 Part 10A", "")),
    ("NASA-HDBK-9999-VOLUME_1 - 2031-12-14-NASA-HDBK-9999A-Vol-1-Rev-Approved", ("NASA-HDBK-9999 Vol 1", "")),
    ("nasa-std-9999-vol-1-rev-c-signature", ("NASA-STD-9999 Vol 1", "Rev.C")),
    ("NASA-STD-9719.24-ANNEX - x", ("NASA-STD-9719.24 Annex", "")),
    ("NASA-HDBK-9739.19-2 - x", ("NASA-HDBK-9739.19-2", "")),
    ("NASA-STD-99999 - 2031-01-28_final", ("NASA-STD-99999", "")),
    ("ECSS-E-ST-99-08C_Rev.2(20April2031)_Annex A", ("ECSS-E-ST-99-08C", "Rev.2")),  # ECSS Word annex: same document
])
def test_parts_volumes_and_annexes(stem, expected):
    assert meta_from_text(stem) == expected


def test_cover_names_volume_and_revision():
    cover = "NASA TECHNICAL HANDBOOK\nNASA-HDBK-9999, VOLUME 2, REVISION A\nSuperseding NASA-HDBK-9999, Baseline\n"
    assert meta_from_text(cover) == ("NASA-HDBK-9999 Vol 2", "Rev.A")


def test_classify():
    assert classify("ECSS-E-ST-32-10C") == {"family": "ECSS", "doc_type": "standard", "discipline": "E-32",
                                           "discipline_name": "structures"}
    assert classify("ECSS-E-HB-31-01 Part 3A")["doc_type"] == "handbook"
    assert classify("ECSS-E-ST-10-03C")["discipline_name"] == "system engineering"
    assert classify("NASA-STD-8739.4A")["discipline"] == "NASA-8700"
    assert classify("NASA-HDBK-7005")["discipline_name"] == "test, analysis and environments"
    assert classify("DEMO-E-ST-99C")["family"] == "other"


def test_without_corpus_only_top_level_is_loaded(tmp_path):
    _txt(tmp_path / "ECSS-E-ST-99-01C_Rev.1.txt")
    _txt(tmp_path / "bundle" / "ECSS-E-ST-99-02C_Rev.1.txt")
    cat = build_catalogue(tmp_path)
    assert {e.doc_id: e.loaded for e in cat.entries} == {"ECSS-E-ST-99-01C": True, "ECSS-E-ST-99-02C": False}
    assert [d.doc_id for d in load_folder(tmp_path)] == ["ECSS-E-ST-99-01C"]


def test_corpus_selects_and_superseded_never_loads(tmp_path):
    _txt(tmp_path / "ECSS-E-ST-99-01C_Rev.1.txt")
    _txt(tmp_path / "bundle" / "ECSS-E-ST-99-02C_Rev.1.txt")
    _txt(tmp_path / "bundle" / "ECSS-Q-ST-99-70C.txt")
    _txt(tmp_path / "bundle" / "superseded HBs" / "ECSS-E-HB-99-23A.txt")
    (tmp_path / "corpus.yaml").write_text("load:\n  - ECSS-E-*\n")
    cat = build_catalogue(tmp_path)
    by_id = {e.doc_id: e for e in cat.entries}
    assert {k for k, e in by_id.items() if e.loaded} == {"ECSS-E-ST-99-01C", "ECSS-E-ST-99-02C"}
    assert by_id["ECSS-E-HB-99-23A"].status == "superseded" and not by_id["ECSS-E-HB-99-23A"].loaded
    assert sorted(d.doc_id for d in load_folder(tmp_path)) == ["ECSS-E-ST-99-01C", "ECSS-E-ST-99-02C"]


def test_top_level_copy_wins_and_alternates_are_kept(tmp_path):
    _txt(tmp_path / "ECSS-E-ST-99-10C_Rev.2.txt")
    _txt(tmp_path / "bundle" / "ECSS-E-ST-99-10C_Rev.2-Corr.1(1August2031).txt")
    _txt(tmp_path / "bundle" / "superseded" / "ECSS-E-ST-99-10C_Rev.1.txt")
    [e] = build_catalogue(tmp_path).entries
    assert e.source == "ECSS-E-ST-99-10C_Rev.2.txt" and e.status == "active"
    assert len(e.alternates) == 2 and e.alternate_issues == ["Rev.1", "Rev.2 Corr.1"]


def test_pdf_and_word_copies_share_one_identity(tmp_path):
    """A Word copy whose text names another standard stays with its PDF (same file name)."""
    (tmp_path / "pdf").mkdir()
    _write_pdf(tmp_path / "pdf" / "ECSS-E-ST-99-31C Rev.1(15October2031).pdf", ["ECSS-E-ST-99-31C Rev.1"])
    (tmp_path / "word").mkdir()
    d = docx.Document()
    d.add_paragraph("This invented standard refers to ECSS-E-ST-99-01C and ECSS-E-ST-99-01C.")
    d.save(tmp_path / "word" / "ECSS-E-ST-99-31C Rev.1(15October2031).docx")
    [e] = build_catalogue(tmp_path, use_cache=False).entries
    assert (e.doc_id, e.issue, e.source) == ("ECSS-E-ST-99-31C", "Rev.1", "pdf/ECSS-E-ST-99-31C Rev.1(15October2031).pdf")
    assert e.alternates == ["word/ECSS-E-ST-99-31C Rev.1(15October2031).docx"]


def test_download_manifest_names_and_titles(tmp_path):
    _txt(tmp_path / "nasa" / "nasa-hdbk-971914.txt")
    manifest = {"standards": [{"doc_no": "NASA-HDBK-9719.14", "title": "Invented Handbook", "date": "2031-07-30",
                               "dest_filename": "nasa-hdbk-971914.txt"}]}
    (tmp_path / "nasa" / "manifest.json").write_text(json.dumps(manifest))
    [e] = build_catalogue(tmp_path).entries
    assert (e.doc_id, e.title, e.date, e.family, e.doc_type) == (
        "NASA-HDBK-9719.14", "Invented Handbook", "2031-07-30", "NASA", "handbook")


def test_identity_cache_is_reused(tmp_path, monkeypatch):
    _write_pdf(tmp_path / "ECSS-E-ST-99-01C_Rev.1.pdf", ["ECSS-E-ST-99-01C Rev.1"])
    build_catalogue(tmp_path)
    from spacestd import catalogue

    monkeypatch.setattr(catalogue, "read_meta", lambda p: pytest.fail(f"re-read {p}"))
    assert build_catalogue(tmp_path).entries[0].doc_id == "ECSS-E-ST-99-01C"


def test_list_documents_filters_and_not_loaded(tmp_path):
    _txt(tmp_path / "ECSS-E-ST-99-01C_Rev.1.txt")
    _txt(tmp_path / "bundle" / "ECSS-E-HB-99-26A.txt")
    _txt(tmp_path / "bundle" / "NASA-STD-9002B.txt")
    cat = build_catalogue(tmp_path)
    index = StandardsIndex(cat.load_documents(), catalogue=cat)
    loaded = tools.list_documents(index)
    assert loaded["count"] == 1 and loaded["documents"][0]["tier"] == "unchecked"
    assert loaded["documents"][0]["family"] == "ECSS" and loaded["documents"][0]["requirement_count"] == 1
    every = tools.list_documents(index, include_not_loaded=True)
    assert {(d["doc_id"], d.get("loaded", True)) for d in every["documents"]} == {
        ("ECSS-E-ST-99-01C", True), ("ECSS-E-HB-99-26A", False), ("NASA-STD-9002B", False)}
    assert [d["doc_id"] for d in tools.list_documents(index, doc_type="handbook", include_not_loaded=True)["documents"]] \
        == ["ECSS-E-HB-99-26A"]
    assert tools.list_documents(index, family="nasa", include_not_loaded=True)["count"] == 1
    cut = tools.list_documents(index, include_not_loaded=True, limit=1)
    assert len(cut["documents"]) == 1 and "truncated" in cut


def test_named_standards_present_but_not_loaded_vs_not_in_folder(tmp_path):
    """Step A6: search_requirements / compare_topic tell 'in the documents folder, not loaded' from 'not there'."""
    _txt(tmp_path / "corpus.yaml", "load:\n  - ECSS-E-ST-99-01*\n")
    _txt(tmp_path / "ECSS-E-ST-99-01C_Rev.1.txt")
    _txt(tmp_path / "bundle" / "NASA-STD-9002B.txt")
    _txt(tmp_path / "bundle" / "ECSS-E-HB-99-20_Part1A.txt")
    _txt(tmp_path / "bundle" / "ECSS-E-HB-99-20_Part2A.txt")
    _txt(tmp_path / "superseded" / "NASA-STD-9003A.txt")
    cat = build_catalogue(tmp_path)
    index = StandardsIndex(cat.load_documents(), catalogue=cat)

    res = tools.search_requirements(index, "invented thing in NASA-STD-9002 and NASA-STD-9001B")
    assert res["results"] and res["not_loaded"] == ["NASA-STD-9002", "NASA-STD-9001B"]
    assert res["in_documents_folder"] == [{"name": "NASA-STD-9002", "documents": [
        {"doc_id": "NASA-STD-9002B", "issue": "", "title": "", "status": "active"}]}]
    assert res["not_in_documents_folder"] == ["NASA-STD-9001B"]
    assert any("In the documents folder but not loaded: NASA-STD-9002." in n for n in res["notes"])
    assert any("Not in the documents folder: NASA-STD-9001B." in n for n in res["notes"])

    # the bare number names every catalogued part; a superseded copy is never loaded
    res = tools.search_requirements(index, "invented thing in ECSS-E-HB-99-20 and NASA-STD-9003A")
    assert [[d["doc_id"] for d in p["documents"]] for p in res["in_documents_folder"]] == [
        ["ECSS-E-HB-99-20 Part 1A", "ECSS-E-HB-99-20 Part 2A"], ["NASA-STD-9003A"]]
    assert "not_in_documents_folder" not in res
    assert any("superseded" in n and "NASA-STD-9003A" in n for n in res["notes"])

    # a loaded standard is not reported, with or without its issue letter
    assert "not_loaded" not in tools.search_requirements(index, "invented thing in ECSS-E-ST-99-01")

    res = tools.compare_topic(index, "invented thing", doc_ids=["ECSS-E-ST-99-01C", "NASA-STD-9002", "NASA-STD-9009"])
    assert [s["doc_id"] for s in res["documents"]] == ["ECSS-E-ST-99-01C"]
    assert res["not_loaded"] == ["NASA-STD-9002", "NASA-STD-9009"]
    assert [p["name"] for p in res["in_documents_folder"]] == ["NASA-STD-9002"]
    assert res["not_in_documents_folder"] == ["NASA-STD-9009"]
    assert any("Do not compare" in n for n in res["notes"])


def test_without_catalogue_not_loaded_is_not_split():
    index = StandardsIndex([])
    res = tools.search_requirements(index, "invented thing in NASA-STD-9002")
    assert res["not_loaded"] == ["NASA-STD-9002"]
    assert "in_documents_folder" not in res and "not_in_documents_folder" not in res
