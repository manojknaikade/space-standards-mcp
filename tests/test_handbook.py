"""Handbook section records (release plan A5) on the invented handbook fixture (ADR-0002)."""

from pathlib import Path

import pytest

from spacestd.index import StandardsIndex
from spacestd.loaders import load_folder
from spacestd.models import Document, Requirement

FIXTURES = Path(__file__).parent / "fixtures"
HB = "ECSS-E-HB-99-01A"


@pytest.fixture(scope="module")
def docs():
    return load_folder(FIXTURES)


@pytest.fixture(scope="module")
def index(docs) -> StandardsIndex:
    return StandardsIndex(docs)


def test_handbook_has_one_guidance_record_per_numbered_section(docs):
    hb = next(d for d in docs if d.doc_id == HB)
    assert [(r.req_id, r.kind) for r in hb.requirements] == [(i, "guidance") for i in ("4.1", "4.2.1", "4.2.2", "4.2.3")]
    assert hb.unparsed == []  # the prose is in the records, not left over
    r = hb.requirements[0]
    assert r.heading_path == ["4 Fairing structure design guidance", "4.1 Background on design factors"]
    assert r.text.count("\n") == 1  # two paragraphs
    assert r.notes == ["The factors named in this handbook are examples only and carry no authority."]


def test_standards_get_no_section_records(docs):
    for d in docs:
        if d.doc_id != HB:
            assert not any(r.req_id == r.clause for r in d.requirements)


def test_get_requirement_by_section_number(index):
    req = index.get(HB, "4.2.1")
    assert req is not None and req.kind == "guidance"
    assert req.citation == f"{HB}, 4.2.1"
    assert index.get(HB, "4.2") is None  # a heading with no prose of its own has no record


def test_standard_requirement_outranks_handbook_section(index):
    # the handbook 4.2.1 repeats the standard's words about separation system qualification
    hits = index.search_hits("payload fairing separation system qualified by test shock measurement", limit=5)
    ids = [(h.requirement.doc_id, h.requirement.req_id) for h in hits]
    assert ids[0] == ("DEMO-E-ST-98C", "4.2.1a")
    assert (HB, "4.2.1") in ids


def test_handbook_weight_lowers_only_handbook_score():
    text = "Fairing panels shall be inspected for disbonds before launch."
    std = Document("ECSS-E-ST-50C", "", "", "", [Requirement("ECSS-E-ST-50C", "", "4.1a", "4.1", text, kind="guidance")])
    hb = Document("ECSS-E-HB-50A", "", "", "", [Requirement("ECSS-E-HB-50A", "", "4.1", "4.1", text, kind="guidance")])
    hits = StandardsIndex([hb, std]).search_hits("fairing panels inspected disbonds", detect_docs=False)
    assert [h.requirement.doc_id for h in hits] == ["ECSS-E-ST-50C", "ECSS-E-HB-50A"]
    assert hits[1].score == pytest.approx(hits[0].score * 0.85, abs=0.002)
