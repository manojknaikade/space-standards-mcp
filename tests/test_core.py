from pathlib import Path

import pytest

from spacestd.index import StandardsIndex
from spacestd.loaders import load_folder
from spacestd.parser import find_references, parse_paragraphs

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def index() -> StandardsIndex:
    return StandardsIndex(load_folder(FIXTURES))


def test_documents_loaded(index):
    docs = {d["doc_id"]: d for d in index.list_documents()}
    assert docs["DEMO-E-ST-99C"]["issue"] == "Rev.1"
    assert docs["DEMO-E-ST-99C"]["requirement_count"] == 6
    assert docs["DEMO NPR 9999.1"]["requirement_count"] == 3


def test_ecss_requirement_ids_and_continuation(index):
    req = index.get("DEMO-E-ST-99C", "5.1.1b")
    assert req is not None
    assert req.text.endswith("including the configuration management tool.")
    assert req.notes == ["The plan can be merged with the project management plan."]
    assert req.citation == "DEMO-E-ST-99C Rev.1, 5.1.1b"
    assert req.heading_path[-1] == "5.1.1 Plan content"


def test_lookup_accepts_doc_prefix_and_case(index):
    assert index.get("demo-e-st-99", "5.2.2A") is not None


def test_nasa_tags(index):
    req = index.get("DEMO NPR 9999.1", "SWE-950")
    assert req is not None
    assert req.clause == "4.1"
    assert "[SWE-950]" not in req.text
    assert "NASA-HDBK-2203" in req.references


def test_references_from_notes(index):
    req = index.get("DEMO-E-ST-99C", "5.2.1a")
    assert "ECSS-Q-ST-80" in req.references
    assert "NASA-STD-8739.8" in req.references
    assert "clause 6.3.5" in req.references


def test_missing_requirement_is_none(index):
    assert index.get("DEMO-E-ST-99C", "9.9.9z") is None
    assert index.get("NOT-A-DOC", "5.1.1a") is None


def test_search_ranks_relevant_requirements(index):
    hits = index.search("unit testing safety-critical")
    ids = [r.req_id for _, r in hits[:2]]
    assert set(ids) == {"5.2.1a", "SWE-950"}


def test_search_filter_by_document(index):
    hits = index.search("unit testing", doc_id="DEMO NPR")
    assert hits and all(r.doc_id == "DEMO NPR 9999.1" for _, r in hits)


def test_find_references_patterns():
    text = "See ECSS-E-ST-40C, NPR 7150.2D and NASA-STD-8739.8, clause 5.4.2a."
    assert find_references(text) == ["ECSS-E-ST-40C", "NPR 7150.2D", "NASA-STD-8739.8", "clause 5.4.2a"]


def test_structures_demo(index):
    req = index.get("DEMO-E-ST-98C", "4.1.2b")
    assert "composite sandwich panels" in req.text
    assert req.notes and "NASA-STD-5001" in req.references
    assert "ECSS-E-HB-32-26A" in index.get("DEMO-E-ST-98C", "4.1.1a").references
    hits = index.search("fairing separation shock qualification")
    assert hits[0][1].req_id == "4.2.1a"


def test_generic_nasa_style_tags(index):
    req = index.get("DEMO-E-ST-98C", "DEMOSTR 7")
    assert req is not None and req.text.startswith("The supplier shall perform an acoustic test")


def test_lettered_items_ignored_before_first_clause():
    reqs = parse_paragraphs(["a. orphan item", "1 Scope", "a. real item"], "X", "")
    assert [r.req_id for r in reqs] == ["1a"]
