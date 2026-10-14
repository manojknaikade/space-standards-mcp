"""Search behaviour (eval run 1 fixes): document detection, BM25 length normalisation, table rows.

All documents here are invented in code (ADR-0002); IDs and numbers mean nothing.
"""

from spacestd.index import StandardsIndex, stem, tokenize
from spacestd.models import Cell, Document, Requirement, Table, TableRow


def req(doc_id, req_id, text, tables=(), kind="requirement"):
    return Requirement(doc_id, "", req_id, req_id.rstrip("abcdefgh"), text, tables=list(tables), kind=kind)


def make_index() -> StandardsIndex:
    base = Document("DEMO-E-ST-50C", "", "", "", [
        req("DEMO-E-ST-50C", "4.1a", "Fairing panels shall be inspected for disbonds."),
    ])
    sub = Document("DEMO-E-ST-50-01C", "", "", "", [
        req("DEMO-E-ST-50-01C", "5.1a", "Fairing panels shall be classified for fracture control."),
        # long record repeating the query words: without length normalisation it would win
        req("DEMO-E-ST-50-01C", "5.2a", " ".join(["Fairing panels and inserts and brackets and fittings"] * 12)),
        req("DEMO-E-ST-50-01C", "5.3a", "Inserts shall be proof tested."),
    ])
    factors = Table(
        "DEMO-STD-7000B", "", "Table 2", "Invented design factors", ["Material", "Approach"],
        ["Yield", "Ultimate"],
        [
            TableRow({"Material": "Metallic", "Approach": "Prototype"},
                     {"Yield": Cell("7.1", 7.1), "Ultimate": Cell("7.2", 7.2)}),
            TableRow({"Material": "Metallic", "Approach": "Protoflight"},
                     {"Yield": Cell("7.3 a", 7.3, ["a"]), "Ultimate": Cell("7.4", 7.4)}),
        ],
        footnotes={"a": "Except pressurised tanks."},
    )
    nasa = Document("DEMO-STD-7000B", "", "", "", [
        req("DEMO-STD-7000B", "DSR 3", "Design factors shall be not less than those in Table 2.", tables=["Table 2"]),
        req("DEMO-STD-7000B", "DSR 4", "Fairing panels shall be tested to qualification levels."),
        req("DEMO-STD-7000B", "DSR 5", "Withdrawn.", tables=["Table 2"], kind="deleted"),
    ], tables=[factors])
    return StandardsIndex([base, sub, nasa])


def ids(hits):
    return [r.req_id for _, r in hits]


def test_tokenize_adds_hyphen_parts():
    toks = tokenize("non-discontinuity payload-fairing Table 4-3")
    assert {"non-discontinuity", "discontinuity", "payload-fairing", "payload", "fairing", "4-3"} <= set(toks)


def test_detect_documents_whole_id_and_issue_letter():
    idx = make_index()
    assert idx.detect_documents("Under DEMO-E-ST-50-01C, how are panels classified?") == ["DEMO-E-ST-50-01C"]
    assert idx.detect_documents("Under DEMO-E-ST-50-01, how?") == ["DEMO-E-ST-50-01C"]
    # the parent ID without letter is not a prefix match for the sub-standard
    assert idx.detect_documents("What does DEMO-E-ST-50 say?") == ["DEMO-E-ST-50C"]
    assert idx.detect_documents("Compare DEMO-STD-7000B and DEMO-E-ST-50-01C.") == ["DEMO-E-ST-50-01C", "DEMO-STD-7000B"]
    assert idx.detect_documents("How are fairing panels inspected?") == []


def test_detect_family_fallback():
    idx = StandardsIndex([
        Document("ECSS-X-ST-01C", "", "", ""), Document("ECSS-X-ST-02C", "", "", ""), Document("NASA-STD-0001", "", "", ""),
    ])
    assert idx.detect_documents("What does ECSS require?") == ["ECSS-X-ST-01C", "ECSS-X-ST-02C"]
    assert idx.detect_documents("Compare ECSS and NASA.") == []
    # a standard ID that is not loaded is not a family mention
    assert idx.detect_documents("What does NASA-HDBK-9999 say?") == []
    assert idx.search("What does NASA-HDBK-9999 say?") == []  # nothing indexed, but no NASA-only filter either


def test_family_named_but_not_loaded_searches_nothing():
    idx = StandardsIndex([Document("NASA-STD-0001", "", "", "", [req("NASA-STD-0001", "R 1", "Panels shall be tested.")])])
    assert ids(idx.search("panels tested")) == ["R 1"]
    assert idx.search("What does ECSS require for panels tested?") == []
    assert ids(idx.search("NASA-HDBK-9999 panels tested")) == ["R 1"]


def test_named_document_restricts_search():
    idx = make_index()
    assert {r.doc_id for _, r in idx.search("fairing panels")} == {"DEMO-E-ST-50C", "DEMO-E-ST-50-01C", "DEMO-STD-7000B"}
    assert {r.doc_id for _, r in idx.search("DEMO-E-ST-50 fairing panels")} == {"DEMO-E-ST-50C"}
    assert {r.doc_id for _, r in idx.search("DEMO-E-ST-50 fairing panels", detect_docs=False)} != {"DEMO-E-ST-50C"}
    # an explicit doc_id wins over the documents named in the query
    assert {r.doc_id for _, r in idx.search("DEMO-E-ST-50 fairing panels", doc_id="DEMO-STD-7000B")} == {"DEMO-STD-7000B"}
    assert idx.search("fairing panels", doc_id="NOT-A-DOC") == []


def test_several_named_documents_are_interleaved():
    hits = make_index().search("fairing panels in DEMO-E-ST-50-01C and DEMO-STD-7000B", limit=2)
    assert {r.doc_id for _, r in hits} == {"DEMO-E-ST-50-01C", "DEMO-STD-7000B"}


def test_length_normalisation_prefers_focused_record():
    hits = make_index().search("fairing panels classified", doc_id="DEMO-E-ST-50-01C")
    assert ids(hits)[0] == "5.1a"


def test_table_row_match_credits_owning_requirement():
    idx = make_index()
    hits = idx.search_hits("metallic protoflight yield factor", doc_id="DEMO-STD-7000B")
    top = hits[0]
    assert top.requirement.req_id == "DSR 3"  # the row words are not in the requirement text
    assert top.row.labels == {"Material": "Metallic", "Approach": "Protoflight"}
    d = top.to_dict()
    assert d["citation"] == "DEMO-STD-7000B, DSR 3"
    assert d["matched_table_row"]["citation"] == "DEMO-STD-7000B, Table 2"
    assert d["matched_table_row"]["cells"]["Yield"]["footnotes"] == ["a"]
    assert "DSR 5" not in ids(idx.search("metallic protoflight", doc_id="DEMO-STD-7000B", limit=10))  # deleted


def test_row_footnotes_are_searchable():
    hits = make_index().search_hits("pressurised tanks", doc_id="DEMO-STD-7000B")
    assert hits and hits[0].row.labels["Approach"] == "Protoflight"


def test_doc_lookup_prefers_exact_id_over_prefix():
    idx = make_index()
    assert idx.get("DEMO-E-ST-50", "4.1a") is not None
    assert idx.get("DEMO-E-ST-50", "5.1a") is None  # 5.1a lives in DEMO-E-ST-50-01C
    assert idx.get("DEMO-E-ST-50-01", "5.1a") is not None


# --------------------------------------------------------------------------- hand test F5 / F6


def test_stem_meets_inflections():
    assert {stem(w) for w in ("test", "tests", "tested", "testing")} == {"test"}
    assert stem("welds") == stem("weld") and stem("requires") == stem("required") == stem("require")
    assert stem("cutting") == "cut" and stem("bodies") == "body" and stem("fairings") == "fairing"
    assert stem("glass") == "glass" and stem("bus") == "bus" and stem("4-3") == "4-3"  # left alone


def test_inflected_query_finds_requirement():
    idx = StandardsIndex([Document("DEMO-STD-8000", "", "", "", [
        req("DEMO-STD-8000", "R 1", "If proof testing is used as the screening technique, document it."),
        req("DEMO-STD-8000", "R 2", "Gizmos shall be painted."),
    ])])
    assert ids(idx.search("proof test screening")) == ["R 1"]


def test_guidance_ranks_below_equal_requirement():
    idx = StandardsIndex([Document("DEMO-STD-8000", "", "", "", [
        req("DEMO-STD-8000", "4.1 guidance 1", "Widgets need a life factor of nine.", kind="guidance"),
        req("DEMO-STD-8000", "R 1", "Widgets need a life factor of nine."),
    ])])
    assert ids(idx.search("widget life factor")) == ["R 1", "4.1 guidance 1"]


def test_not_loaded_standards_are_reported():
    idx = make_index()
    res = idx.search_response("What does DEMO-STD-9999 or NASA-STD-7003 require for fairing panels?")
    assert res["not_loaded"] == ["NASA-STD-7003"]  # only IDs of known families are recognised
    assert "Not loaded" in res["notes"][0] and res["results"]
    assert "not_loaded" not in idx.search_response("How are fairing panels inspected?")
    assert idx.mentioned_not_loaded("ECSS-E-ST-33-01 and ECSS-Q-ST-70-71C") == ["ECSS-E-ST-33-01", "ECSS-Q-ST-70-71C"]


def test_weak_named_document_shows_elsewhere():
    idx = StandardsIndex([
        Document("ECSS-E-ST-90-01C", "", "", "", [req("ECSS-E-ST-90-01C", "1.1a", "Coatings shall be bonded to the substrate.")]),
        Document("ECSS-E-ST-90C", "", "", "", [
            req("ECSS-E-ST-90C", "4.1a", "Adhesive bonded joints shall be analysed with adhesive allowables."),
            req("ECSS-E-ST-90C", "4.2a", "Bonded joints in sandwich panels shall be verified."),
        ]),
    ])
    res = idx.search_response("What does ECSS-E-ST-90-01 require for adhesive bonded joints?")
    assert [h["req_id"] for h in res["results"]] == ["1.1a"]  # the filter still applies
    assert [h["req_id"] for h in res["elsewhere"]][0] == "4.1a" and "weakly" in res["notes"][-1]
    good = idx.search_response("What does ECSS-E-ST-90 require for adhesive bonded joints?")
    assert "elsewhere" not in good and good["results"][0]["req_id"] == "4.1a"


def compare_index() -> StandardsIndex:
    factors = Table("NASA-STD-0001", "B", "Table 1", "Invented design factors", ["Material"], ["Ultimate"],
                    [TableRow({"Material": "Metallic"}, {"Ultimate": Cell("7.5", 7.5)})])
    return StandardsIndex([
        Document("ECSS-X-ST-01C", "Rev.1", "", "", [
            req("ECSS-X-ST-01C", "4.1a", "The ultimate design factor of metallic structures shall be justified."),
            req("ECSS-X-ST-01C", "4.2a", "Fracture critical parts shall be listed."),
        ]),
        Document("ECSS-X-ST-02C", "", "", "", [req("ECSS-X-ST-02C", "3.1a", "Software shall be documented.")]),
        Document("NASA-STD-0001", "B", "", "", [
            req("NASA-STD-0001", "R 1", "Ultimate design factors shall be not less than in Table 1.", tables=["Table 1"]),
        ], tables=[factors]),
    ])


def test_compare_topic_sections_per_document():
    res = compare_index().compare_topic("ECSS vs NASA: ultimate design factor for metallic structure")
    secs = {s["doc_id"]: s for s in res["documents"]}
    assert [s["family"] for s in res["documents"]] == ["ECSS", "ECSS", "NASA"]
    assert secs["ECSS-X-ST-01C"]["results"][0]["req_id"] == "4.1a" and secs["ECSS-X-ST-01C"]["coverage"] == "ok"
    assert secs["NASA-STD-0001"]["results"][0]["matched_table_row"]["citation"] == "NASA-STD-0001 B, Table 1"
    assert secs["ECSS-X-ST-02C"]["coverage"] == "none" and "weak" in res["notes"][-1]


def test_compare_topic_named_and_requested_documents():
    idx = compare_index()
    res = idx.compare_topic("ultimate design factor in ECSS-X-ST-01 and NASA-STD-0001")
    assert [s["doc_id"] for s in res["documents"]] == ["ECSS-X-ST-01C", "NASA-STD-0001"]
    res = idx.compare_topic("ultimate design factor", doc_ids=["NASA-STD-0001", "ECSS-X-ST-01", "NASA-STD-0099"])
    assert [s["doc_id"] for s in res["documents"]] == ["ECSS-X-ST-01C", "NASA-STD-0001"]  # ECSS first
    assert res["not_loaded"] == ["NASA-STD-0099"]


def test_neighbours_show_adjacent_records_of_the_same_clause():
    doc = Document("DEMO-E-ST-60C", "", "", "", [
        req("DEMO-E-ST-60C", "6.1a", "Fail-safe items shall be evaluated per the flow chart."),
        req("DEMO-E-ST-60C", "6.1b", "Remaining structure shall carry limit loads after a failure."),
        req("DEMO-E-ST-60C", "6.1c", "No released fragment shall create a hazard."),
        req("DEMO-E-ST-60C", "6.1d", "Withdrawn.", kind="deleted"),
        req("DEMO-E-ST-60C", "6.1e", "Items shall be inspectable after the event."),
        req("DEMO-E-ST-60C", "6.2a", "Unrelated clause about markings."),
    ])
    index = StandardsIndex([doc])
    assert [r.req_id for r in index.neighbours(index.get("DEMO-E-ST-60C", "6.1c"))] == ["6.1b", "6.1e"]
    assert [r.req_id for r in index.neighbours(index.get("DEMO-E-ST-60C", "6.1a"))] == ["6.1b"]
    assert index.neighbours(index.get("DEMO-E-ST-60C", "6.2a")) == []

    res = index.search_response("remaining structure limit loads failure", limit=1)
    top = res["results"][0]
    assert top["req_id"] == "6.1b"
    assert [n["req_id"] for n in top["neighbours"]] == ["6.1a", "6.1c"]
    assert top["neighbours"][1]["citation"] == "DEMO-E-ST-60C, 6.1c" and top["neighbours"][1]["text"]
    # a record already shown as a hit, or as an earlier hit's neighbour, is not repeated
    res = index.search_response("fail-safe remaining structure released fragment", limit=3)
    shown = [r["req_id"] for r in res["results"]] + [n["req_id"] for r in res["results"] for n in r.get("neighbours", [])]
    assert len(shown) == len(set(shown))


def _ownerless_index() -> StandardsIndex:
    orphan = Table("DEMO-STD-7100A", "", "Table 6", "Invented appendix margins", ["Item"], ["Margin"],
                   [TableRow({"Item": "Zebra strut"}, {"Margin": Cell("0.9", 0.9)})], page=41)
    doc = Document("DEMO-STD-7100A", "", "", "", [
        req("DEMO-STD-7100A", "DSR 1", "Panels shall be inspected."),
    ], tables=[orphan])
    return StandardsIndex([doc, make_index().documents[2]])


def test_ownerless_table_is_searchable_through_a_table_record():
    idx = _ownerless_index()
    doc = next(d for d in idx.documents if d.doc_id == "DEMO-STD-7100A")
    assert [r.req_id for r in doc.requirements] == ["DSR 1"]  # the synthetic owner is not a record
    top = idx.search_hits("zebra strut margin", limit=3)[0]
    assert top.requirement.kind == "table"
    assert top.requirement.citation == top.table.citation == "DEMO-STD-7100A, Table 6"
    assert idx.neighbours(top.requirement) == []
    d = idx.search_response("zebra strut margin")["results"][0]
    assert d["kind"] == "table" and d["matched_table_row"]["citation"] == "DEMO-STD-7100A, Table 6"
    assert d["matched_table_row"]["page"] == 41
    assert idx.get("DEMO-STD-7100A", "Table 6") is None
    same = idx.search_hits("zebra strut margin", limit=3)[0]
    assert same.requirement is top.requirement  # created once per table


def test_owned_tables_keep_their_owners():
    idx = make_index()
    hits = idx.search_hits("prototype yield ultimate design factors", doc_id="DEMO-STD-7000B", limit=5)
    assert [h.requirement.req_id for h in hits if h.table] == ["DSR 3"]
    assert all(h.requirement.kind != "table" for h in hits)


def test_requirements_matrix_rows_are_not_indexed():
    # run 12: an ownerless requirements matrix restating '[DSR 1] ...' outranked the record itself
    matrix = Table("DEMO-STD-7100A", "", "Table 9", "Invented compliance matrix", ["Section"], ["Requirement"],
                   [TableRow({"Section": "4.1"}, {"Requirement": Cell("[DSR 1] Zebra panels shall be inspected.")}),
                    TableRow({"Section": "4.2"}, {"Requirement": Cell("Zebra struts are listed here.")})], page=50)
    doc = Document("DEMO-STD-7100A", "", "", "", [req("DEMO-STD-7100A", "DSR 1", "Zebra panels shall be inspected.")],
                   tables=[matrix])
    idx = StandardsIndex([doc])
    hits = idx.search_hits("zebra panels inspected", limit=5)
    assert hits[0].requirement.req_id == "DSR 1" and hits[0].table is None
    assert idx.search_hits("zebra struts listed", limit=5)[0].requirement.kind == "table"  # untagged rows still indexed
