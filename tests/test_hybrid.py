"""Hybrid search (BM25 + embeddings, reciprocal rank fusion).

The embedder is invented: words map to a few "concept" dimensions so that paraphrases meet without
sharing a word. All documents are invented in code (ADR-0002); IDs and numbers mean nothing.
"""

import sys
import types

import pytest

np = pytest.importorskip("numpy")

from spacestd.embeddings import FastEmbedder, load_embedder  # noqa: E402
from spacestd.index import StandardsIndex  # noqa: E402
from spacestd.models import Cell, Document, Requirement, Table, TableRow  # noqa: E402

CONCEPTS = {
    "debris": 0, "fragment": 0, "fragments": 0, "pieces": 0,
    "release": 1, "released": 1, "detach": 1, "liberated": 1, "shed": 1,
    "panel": 2, "panels": 2, "fairing": 2, "shroud": 2,
    "inspect": 3, "inspected": 3, "examined": 3, "nondestructive": 3,
    "factor": 4, "factors": 4, "margin": 4, "multiplier": 4,
    "composite": 5, "laminate": 5,
}


class ConceptEmbedder:
    name = "concept-test"

    def __init__(self):
        self.calls = 0

    def _vec(self, text):
        v = np.zeros(len(set(CONCEPTS.values())) + 1, dtype=np.float32)
        for w in text.lower().replace(".", " ").replace(",", " ").split():
            if w in CONCEPTS:
                v[CONCEPTS[w]] += 1
        v[-1] = 0.01  # never all-zero
        return v / np.linalg.norm(v)

    def embed_documents(self, texts):
        self.calls += 1
        return np.stack([self._vec(t) for t in texts])

    def embed_query(self, text):
        return self._vec(text)


def req(doc_id, req_id, text, tables=(), kind="requirement"):
    return Requirement(doc_id, "", req_id, req_id.rstrip("abcdefgh"), text, tables=list(tables), kind=kind)


def docs():
    ecss = Document("DEMO-E-ST-60C", "", "", "", [
        req("DEMO-E-ST-60C", "4.1a", "Shroud parts shall not detach during separation."),
        req("DEMO-E-ST-60C", "4.2a", "Panels shall be examined after acoustic test."),
        req("DEMO-E-ST-60C", "4.3a", "Bolts shall be torqued per the drawing."),
    ])
    factors = Table("DEMO-STD-8000A", "", "Table 1", "Invented multipliers", ["Material"], ["Yield"],
                    [TableRow({"Material": "Laminate"}, {"Yield": Cell("8.1", 8.1)})])
    nasa = Document("DEMO-STD-8000A", "", "", "", [
        req("DEMO-STD-8000A", "DR 1", "Multipliers shall be not less than those in Table 1.", tables=["Table 1"]),
        req("DEMO-STD-8000A", "DR 2", "Fairing panels shall be inspected for disbonds."),
    ], tables=[factors])
    return [ecss, nasa]


def keys(hits):
    return [f"{h.requirement.doc_id}|{h.requirement.req_id}" for h in hits]


def test_paraphrase_found_only_with_embeddings():
    q = "Can debris pieces be liberated at staging?"
    assert "DEMO-E-ST-60C|4.1a" not in keys(StandardsIndex(docs()).search_hits(q, limit=5))
    hybrid = StandardsIndex(docs(), ConceptEmbedder())
    top = hybrid.search_hits(q, limit=2)
    assert keys(top)[0] == "DEMO-E-ST-60C|4.1a"
    h = top[0]
    assert h.lexical == 0 and h.dense is not None and h.dense > 0
    d = h.to_dict()
    assert {"lexical_score", "dense_score", "citation"} <= set(d)


def test_both_rankings_agree_scores_highest():
    hybrid = StandardsIndex(docs(), ConceptEmbedder())
    top = hybrid.search_hits("fairing panels inspected", limit=3)
    assert keys(top)[0] == "DEMO-STD-8000A|DR 2"
    assert top[0].score > 1.5  # first in both rankings: about 2 on the RRF scale
    assert top[0].lexical > 0


def test_bm25_only_output_unchanged():
    hits = StandardsIndex(docs()).search_hits("fairing panels inspected", limit=3)
    assert hits[0].score == hits[0].lexical
    assert "dense_score" not in hits[0].to_dict()


def test_dense_respects_document_filter():
    hybrid = StandardsIndex(docs(), ConceptEmbedder())
    q = "debris release from the shroud"
    assert {h.requirement.doc_id for h in hybrid.search_hits(q, doc_id="DEMO-STD-8000A", limit=5)} == {"DEMO-STD-8000A"}
    assert hybrid.search_hits(q, doc_id="NOT-LOADED-1", limit=5) == []


def test_dense_table_row_credited_to_owner():
    hybrid = StandardsIndex(docs(), ConceptEmbedder())
    top = hybrid.search_hits("composite margin", limit=1)
    assert keys(top) == ["DEMO-STD-8000A|DR 1"]
    assert top[0].table is not None and top[0].row.labels == {"Material": "Laminate"}


def test_coverage_stays_lexical():
    """Dense-only hits never make a document look like it covers the topic."""
    plain, hybrid = StandardsIndex(docs()), StandardsIndex(docs(), ConceptEmbedder())
    topic = "bolts torqued"
    for idx in (plain, hybrid):
        cov = {s["doc_id"]: s["coverage"] for s in idx.compare_topic(topic)["documents"]}
        assert cov == {"DEMO-E-ST-60C": "ok", "DEMO-STD-8000A": "none"}
    q = "DEMO-STD-8000A: are bolts torqued?"
    assert set(plain.search_response(q)) == set(hybrid.search_response(q))
    assert "elsewhere" in hybrid.search_response(q)


def test_empty_query_and_no_documents():
    assert StandardsIndex(docs(), ConceptEmbedder()).search_hits("   ") == []
    empty = StandardsIndex([], ConceptEmbedder())
    assert not empty.hybrid and empty.search_hits("debris") == []


def test_load_embedder_off():
    assert load_embedder(None) is None and load_embedder("none") is None


def test_fastembedder_caches_vectors(tmp_path, monkeypatch):
    seen = []

    class FakeTextEmbedding:
        def __init__(self, model):
            self.model = model

        def embed(self, texts):
            seen.extend(texts)
            return [np.array([len(t), 1.0], dtype=np.float32) for t in texts]

    monkeypatch.setitem(sys.modules, "fastembed", types.SimpleNamespace(TextEmbedding=FakeTextEmbedding))
    e = FastEmbedder("org/model", cache_dir=tmp_path)
    v = e.embed_documents(["abc", "de", "abc"])
    assert v.shape == (3, 2) and np.allclose(np.linalg.norm(v, axis=1), 1)
    assert seen == ["abc", "de"]
    # a new process reads the cache and only embeds the new text
    seen.clear()
    e2 = FastEmbedder("org/model", cache_dir=tmp_path)
    assert np.allclose(e2.embed_documents(["de", "abc", "xyz"])[:2], v[[1, 0]])
    assert seen == ["xyz"]
    assert e2.embed_query("abc").shape == (2,)


class LengthReranker:
    """Invented cross-encoder: prefers the shortest record text."""

    name = "length-test"

    def score(self, query, texts):
        self.seen = texts
        return [-len(t) for t in texts]


def test_reranker_reorders_top_only_and_keeps_coverage():
    rr = LengthReranker()
    idx = StandardsIndex(docs(), reranker=rr)
    hits = idx.search_hits("panels", limit=5)
    assert [h.rerank for h in hits] == sorted((h.rerank for h in hits), reverse=True)
    assert all(h.lexical > 0 for h in hits) and "rerank_score" in hits[0].to_dict()
    # a hit found through a table row is reranked with the row's text
    idx.search_hits("laminate", limit=1)
    assert any("Laminate" in t for t in rr.seen)
    cov = {s["doc_id"]: s["coverage"] for s in idx.compare_topic("bolts torqued")["documents"]}
    assert cov == {"DEMO-E-ST-60C": "ok", "DEMO-STD-8000A": "none"}
