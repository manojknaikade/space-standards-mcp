"""Parts, volumes and annexes in document IDs (step A4): query detection, `not_loaded` and the invented-ID check.

All documents here are invented in code (ADR-0002); the numbers only have the shape of real multi-part IDs
('X Part 1A', 'X Vol 1', 'X Annex') and mean nothing.
"""

from spacestd.citations import CitationChecker
from spacestd.index import StandardsIndex
from spacestd.models import Document, Requirement

HB, VOL, STD = "ECSS-E-HB-90-20", "NASA-HDBK-9010", "NASA-STD-9719.24"


def doc(doc_id, *records):
    return Document(doc_id, "", "", "", [Requirement(doc_id, "", rid, rid.rstrip("abc"), text) for rid, text in records])


def make_index() -> StandardsIndex:
    return StandardsIndex([
        doc(f"{HB} Part 1A", ("4.1a", "Panels shall be checked for invented flaws."), ("4.2a", "Shared clause one.")),
        doc(f"{HB} Part 2A", ("5.1a", "Panels shall be weighed on invented scales."), ("4.2a", "Shared clause two.")),
        doc(f"{HB} Part 10A", ("6.1a", "Panels shall be painted an invented colour.")),
        doc(f"{VOL} Vol 1", ("VR 1", "Bolts shall be torqued to invented values.")),
        doc(f"{VOL} Vol 10", ("VR 9", "Nuts shall be locked by invented means.")),
        doc(STD, ("AR 1", "Hazards shall be listed in an invented log.")),
        doc(f"{STD} Annex", ("AR 2", "Annex hazards shall be ranked by invented rules.")),
        doc("ECSS-X-ST-01C", ("4.1a", "Coatings shall be invented.")),
    ])


def detect(idx, q):
    return idx._detect(q)[0]


def test_part_volume_and_annex_detected_in_any_spelling():
    idx = make_index()
    for q in (f"What does {HB} Part 1A say about panels?", f"{HB} part 1 panels", f"{HB}_Part1A panels",
              f"{HB}-PART-1A panels"):
        assert detect(idx, q) == [f"{HB}-PART-1A"], q
    for q in (f"{VOL} Vol 1 bolts", f"{VOL} Volume 1 bolts", f"{VOL} Vol. 1 bolts", f"{VOL}-VOL-1 bolts"):
        assert detect(idx, q) == [f"{VOL}-VOL-1"], q
    assert detect(idx, f"{HB} Part 10A panels") == [f"{HB}-PART-10A"]  # not Part 1A
    assert detect(idx, f"{VOL} Volume 10 nuts") == [f"{VOL}-VOL-10"]
    assert detect(idx, f"{STD} Annex hazards") == [f"{STD}-ANNEX"]  # not the standard itself


def test_bare_number_names_every_part_unless_it_is_loaded_itself():
    idx = make_index()
    assert detect(idx, f"{HB} panels") == [f"{HB}-PART-1A", f"{HB}-PART-2A", f"{HB}-PART-10A"]
    assert detect(idx, f"{VOL} bolts") == [f"{VOL}-VOL-1", f"{VOL}-VOL-10"]
    assert detect(idx, f"{STD} hazards") == [STD]  # the standard is loaded: its annex is not meant
    assert idx._match_doc(f"{VOL} Vol 1") == [f"{VOL}-VOL-1"]  # a prefix stops at a number
    assert idx.get(HB, "5.1a").doc_id == f"{HB} Part 2A"


def test_ecss_annex_letter_is_inside_the_standard():
    idx = make_index()
    assert detect(idx, "ECSS-X-ST-01C Annex A coatings") == ["ECSS-X-ST-01C"]
    assert idx.mentioned_not_loaded("ECSS-X-ST-01C Annex A coatings") == []


def test_parts_and_volumes_that_are_not_loaded_are_reported():
    idx = make_index()
    q = f"Compare {HB} Part 3A, {VOL} Vol 2, NASA-STD-9719.25 Annex and NASA-STD-90001 for panels"
    assert idx.mentioned_not_loaded(q) == [f"{HB} Part 3A", f"{VOL} Vol 2", "NASA-STD-9719.25 Annex",
                                            "NASA-STD-90001"]
    assert detect(idx, f"{HB} Part 3A panels") is None  # another part is not a mention of the loaded ones
    res = idx.search_response(f"What does {HB} Part 3A say about panels?")
    assert res["not_loaded"] == [f"{HB} Part 3A"] and res["results"]
    assert idx.mentioned_not_loaded(f"{HB} Part 1A, {VOL} Volume 1 and {STD} Annex") == []


def test_compare_topic_strips_part_names_from_the_subject():
    res = make_index().compare_topic("panels", doc_ids=[f"{HB} Part 1A", f"{HB} Part 3A"])
    assert [s["doc_id"] for s in res["documents"]] == [f"{HB} Part 1A"] and res["not_loaded"] == [f"{HB} Part 3A"]
    res = make_index().compare_topic(f"panels in {HB} Part 1A vs {HB} Part 2A")
    assert [s["doc_id"] for s in res["documents"]] == [f"{HB} Part 1A", f"{HB} Part 2A"]


def test_citations_resolve_to_the_named_part():
    checker = CitationChecker(make_index())
    res = checker.check(f"{HB} Part 2A 4.2a and {VOL} Volume 1 VR 1 say so; {STD} Annex AR 2 too.")
    assert res.cited_keys == {f"{HB} Part 2A|4.2a", f"{VOL} Vol 1|VR 1", f"{STD} Annex|AR 2"}
    assert res.invented == [] and res.ungrounded == []  # '2', '1' of the part names are not values
    # the bare number: an ID in only one part resolves to it, one in several stays ambiguous
    res = checker.check(f"{HB} 5.1a and {HB} 4.2a.")
    assert res.cited_keys == {f"{HB} Part 2A|5.1a"} and res.to_dict()["ambiguous"] == ["4.2a"]


def test_ids_from_parts_that_are_not_loaded_are_external_not_invented():
    checker = CitationChecker(make_index())
    for ans in (f"{HB} Part 3A 7.7a requires it.", f"{VOL} Vol 2 VR 7 requires it.",
                "NASA-STD-9719.25 Annex AR 7 requires it."):
        res = checker.check(ans)
        assert res.invented == [] and res.cited_keys == set() and res.to_dict()["external"], ans
    # a loaded part named in between takes over again
    res = checker.check(f"{HB} Part 3A is not loaded; {HB} Part 1A 7.7a says so.")
    assert res.invented == ["7.7a"]
