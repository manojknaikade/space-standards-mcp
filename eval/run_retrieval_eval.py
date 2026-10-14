"""Retrieval evaluation: does search put the expected requirements in the top k?

Usage:
    python eval/run_retrieval_eval.py --docs tests/fixtures
    python eval/run_retrieval_eval.py --docs documents --k 5
    python eval/run_retrieval_eval.py --docs documents --embed default [--rerank default]   # hybrid (".[embed]")

Questions with `expected_tables` are also scored on tables: a table counts as found by a top-k hit when
the hit matched one of its rows ("row hit") or the hit's requirement points to it ("reachable": a client
gets the numbers with get_table).

Answer-level evaluation (LLM answers, citation checks, judge): eval/run_answer_eval.py.
"""

from __future__ import annotations

import argparse
from itertools import zip_longest
from pathlib import Path

import yaml

from spacestd.citations import norm_key
from spacestd.embeddings import load_embedder, load_reranker
from spacestd.index import DENSE_WEIGHT, StandardsIndex
from spacestd.loaders import load_folder


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="documents")
    ap.add_argument("--questions", default=str(Path(__file__).with_name("questions.yaml")))
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--oracle-doc", action="store_true",
                    help="diagnostic only: restrict each search to the document(s) of its expected IDs")
    ap.add_argument("--no-doc-detect", action="store_true",
                    help="ablation: do not restrict the search to the documents named in the question")
    ap.add_argument("--embed", help="hybrid search: fastembed model name, or 'default'")
    ap.add_argument("--rerank", help="cross-encoder reranker: fastembed model name, or 'default'")
    ap.add_argument("--neighbours", action="store_true",
                    help="also count the neighbours shown with each top-k hit (same clause, adjacent records)")
    ap.add_argument("--dense-weight", type=float, default=DENSE_WEIGHT, help="hybrid: weight of the embedding ranking in RRF")
    args = ap.parse_args()

    index = StandardsIndex(load_folder(Path(args.docs)), embedder=load_embedder(args.embed),
                           dense_weight=args.dense_weight, reranker=load_reranker(args.rerank))
    questions = yaml.safe_load(Path(args.questions).read_text(encoding="utf-8"))

    scored = hits = 0
    table_scores = []  # (row hit, reachable) recall per question with expected tables
    for q in questions:
        tables = [norm_key(t) for t in q.get("expected_tables") or []]
        if tables and not args.oracle_doc:
            top = index.search_hits(q["question"], limit=args.k, detect_docs=not args.no_doc_detect)
            rows = {norm_key(f"{h.table.doc_id}|{h.table.table_id}") for h in top if h.table}
            reach = rows | {norm_key(f"{h.requirement.doc_id}|{t}") for h in top for t in h.requirement.tables}
            table_scores.append((sum(t in rows for t in tables) / len(tables),
                                 sum(t in reach for t in tables) / len(tables)))
            if table_scores[-1][1] < 1:
                print(f"TABLE MISS {q['id']}: {sorted(set(tables) - reach)} not reachable from the top {args.k}")
        expected = set(q.get("expected_ids") or [])
        if not expected:
            continue  # not_covered questions are judged at answer level
        if args.oracle_doc:
            # one ranking per expected document, interleaved so each document gets a share of the top k
            per_doc = [[f"{r.doc_id}|{r.req_id}" for _, r in index.search(q["question"], doc, limit=100_000)]
                       for doc in sorted({e.split("|")[0] for e in expected})]
            ranking = [e for group in zip_longest(*per_doc) for e in group if e]
        else:
            ranking = [f"{r.doc_id}|{r.req_id}"
                       for _, r in index.search(q["question"], limit=100_000, detect_docs=not args.no_doc_detect)]
        found = set(ranking[: args.k])
        if args.neighbours and not args.oracle_doc:
            top = index.search_hits(q["question"], limit=args.k, detect_docs=not args.no_doc_detect)
            found |= {f"{n.doc_id}|{n.req_id}" for h in top for n in index.neighbours(h.requirement)}
        recall = len(expected & found) / len(expected)
        scored += 1
        hits += recall
        status = "OK " if recall == 1 else "MISS"
        # rank of each missing ID in the full ranking ("-" = not retrieved at all, or not parsed)
        missing = {e: (ranking.index(e) + 1 if e in ranking else "-") for e in sorted(expected - found)}
        extra = ""
        if missing and not args.oracle_doc and not args.no_doc_detect:
            # the tool response also offers 'elsewhere' hits when the named document matches weakly
            other = {f"{h['doc_id']}|{h['req_id']}" for h in index.search_response(q["question"]).get("elsewhere", [])}
            if other & set(missing):
                extra = f"  in 'elsewhere': {sorted(other & set(missing))}"
        print(f"{status} {q['id']}: recall@{args.k}={recall:.2f}  missing(rank)={missing}{extra}")

    if scored:
        print(f"\nMean recall@{args.k}: {hits / scored:.2f} over {scored} questions")
    if table_scores:
        n = len(table_scores)
        print(f"Table recall@{args.k} over {n} questions: row hit {sum(r for r, _ in table_scores) / n:.2f}, "
              f"reachable {sum(r for _, r in table_scores) / n:.2f}")


if __name__ == "__main__":
    main()
