"""Coverage evaluation: does the server, on its own, lead to the right standard, clause and revision?

    python eval/run_coverage_eval.py --docs documents                      # prints the score
    python eval/run_coverage_eval.py --docs documents --save eval/coverage_scores/<name>.json
    python eval/run_coverage_eval.py --docs documents --compare eval/coverage_scores/baseline.json

Deterministic and LLM-free, so it can run after every commit. It plays a fixed, minimal client against the
tool functions the MCP server exposes (`spacestd.tools`): one `search_requirements` call with the question as
typed, then `get_requirement` for the expected IDs. Questions: eval/coverage_questions.yaml (all ECSS branches
and the NASA families; expected standard, issue, clause and requirement IDs read from the source documents).

Per covered question (each 0..1, averaged over the expected entries):
  S  standard   the expected standard is among the top-k hits (with their neighbours)
  C  clause     a record of the expected clause (or one of the expected requirement IDs) is among them
  L  lookup     each expected requirement ID resolves with get_requirement, on the expected page (+-1);
                with no requirement IDs, the clause itself resolves (record or outline)
  R  revision   the server reports the expected issue for that standard, and an edition date that matches
                the cover date
  score = 0.25 S + 0.35 C + 0.20 L + 0.20 R; S and C count as 0 when the response says `coverage: none`
  (the server would be telling the client the topic is not covered).
Per not_covered question:  1 when the response says so (`coverage: none`, no results, or the named standard
  is reported `not_loaded` or among `external_standards`), 0.5 for `coverage: weak`, else 0.
Per revision question (the question names an issue that is not the loaded one): 1 when the search response
  reports the mismatch (`issue_mismatch`) and get_requirement for that issue does not silently answer.

The total is the mean over all questions, times 100. Document ranking (the expected standard in the top 5 of
`find_standards` for the question as typed), tables (`expected_tables` reachable from the top-k) and
edition completeness (hits whose citation data has document, ID and an issue or date) are reported beside it.
The LLM answer eval (eval/run_answer_eval.py --questions eval/coverage_questions.yaml) measures the answers.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import yaml

from spacestd import tools
from spacestd.catalogue import build_catalogue
from spacestd.citations import norm_key
from spacestd.index import StandardsIndex

HERE = Path(__file__).parent
WEIGHTS = {"S": 0.25, "C": 0.35, "L": 0.20, "R": 0.20}
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
     "november", "december"], 1)}
DATE_RES = [
    re.compile(r"(?P<d>\d{1,2})\s*(?P<mon>[A-Za-z]{3,9})\.?\s*(?P<y>(?:19|20)\d{2})"),  # 31 July 2008
    re.compile(r"(?P<mon>[A-Za-z]{3,9})\.?\s+(?P<d>\d{1,2}),?\s+(?P<y>(?:19|20)\d{2})"),  # July 31, 2008
    re.compile(r"(?P<y>(?:19|20)\d{2})-(?P<m>\d{2})-(?P<d>\d{2})"),  # 2008-07-31
    re.compile(r"(?P<m>\d{1,2})[/-](?P<d>\d{1,2})[/-](?P<y>(?:19|20)\d{2})"),  # 07/31/2008 (US order)
]


def parse_dates(text: str) -> list[tuple[int, int, int]]:
    """(year, month, day) of every date in `text`, in the forms covers and manifests use."""
    out = []
    for rx in DATE_RES:
        for m in rx.finditer(text or ""):
            g = m.groupdict()
            month = int(g["m"]) if g.get("m") else next(
                (n for name, n in MONTHS.items() if name.startswith(g["mon"].lower()[:3])), 0)
            if 1 <= month <= 12:
                out.append((int(g["y"]), month, int(g["d"])))
    return out


def _norm_id(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def _records(resp: dict) -> list[dict]:
    """The records a client reads first: the hits and their neighbours (not `elsewhere`)."""
    out = []
    for h in resp.get("results", []):
        out.append(h)
        out += h.get("neighbours", [])
    return out


def _in_clause(rec: dict, clause: str) -> bool:
    c = _norm_id(rec.get("clause", ""))
    want = _norm_id(clause)
    if not want:
        return False
    for have in (c, _norm_id(rec.get("req_id", ""))):
        if have == want or (have.startswith(want) and have[len(want):len(want) + 1].isalpha()):
            return True
    return False


def _edition_ok(rec: dict, exp: dict) -> bool:
    if (rec.get("issue") or "") != (exp.get("issue") or ""):
        return False
    # a NASA cover can print several dates (change approved, revalidated): any of them is this edition's
    want = {d[:2] for d in parse_dates(exp.get("cover_issue", ""))}
    if not want:
        return True
    have = parse_dates(str(rec.get("issue_date", "")))
    return bool(have) and have[0][:2] in want


def _tables_reached(recs: list[dict]) -> set[str]:
    out = set()
    for r in recs:
        row = r.get("matched_table_row")
        if row:
            out.add(norm_key(f"{r['doc_id']}|{row['table_id']}"))
        out |= {norm_key(f"{r['doc_id']}|{t}") for t in r.get("tables", [])}
        if r.get("kind") == "table":
            out.add(norm_key(f"{r['doc_id']}|{r['req_id']}"))
    return out


def score_covered(index: StandardsIndex, q: dict, resp: dict) -> dict:
    recs = _records(resp)
    told_none = resp.get("coverage") == "none"
    s = c = lk = r = 0.0
    detail = []
    for e in q["expected"]:
        mine = [x for x in recs if x.get("doc_id") == e["doc_id"]]
        req_ids = [_norm_id(i) for i in e.get("req_ids") or []]
        e_s = bool(mine) and not told_none
        e_c = not told_none and any(_norm_id(x.get("req_id", "")) in req_ids or _in_clause(x, e.get("clause", ""))
                                    for x in mine)
        looked = []
        for rid in e.get("req_ids") or []:
            g = tools.get_requirement(index, e["doc_id"], rid)
            page_ok = not e.get("page") or (bool(g.get("page")) and abs(g["page"] - e["page"]) <= 1)
            ok = bool(g.get("found")) and page_ok
            looked.append((rid, ok, g))
        if e.get("req_ids"):
            e_l = sum(ok for _, ok, _ in looked) / len(looked)
        else:  # handbook prose, definitions: the clause itself must be reachable
            g = tools.get_requirement(index, e["doc_id"], e.get("clause", ""))
            o = tools.get_section_outline(index, e["doc_id"], e.get("clause", "")) if e.get("clause") else {}
            e_l = float(bool(g.get("found")) or bool(o.get("found") and o.get("records")))
            looked.append((e.get("clause", ""), bool(e_l), g))
        meta = mine or [g for _, _, g in looked if g.get("found")]
        if not meta:
            docs = tools.list_documents(index, query=e["doc_id"]).get("documents", [])
            meta = [d for d in docs if d.get("doc_id") == e["doc_id"]]
        e_r = bool(meta) and _edition_ok(meta[0], e)
        s, c, lk, r = s + e_s, c + e_c, lk + e_l, r + e_r
        miss = [rid for rid, ok, _ in looked if not ok]
        detail.append({"doc_id": e["doc_id"], "S": e_s, "C": e_c, "L": round(e_l, 2), "R": e_r, "lookup_miss": miss})
    n = len(q["expected"])
    parts = {"S": s / n, "C": c / n, "L": lk / n, "R": r / n}
    out = {**{k: round(v, 3) for k, v in parts.items()},
           "score": round(sum(WEIGHTS[k] * v for k, v in parts.items()), 3), "detail": detail}
    tabs = [norm_key(t) for t in q.get("expected_tables") or []]
    if tabs:
        reach = _tables_reached(recs)
        out["T"] = round(sum(t in reach for t in tabs) / len(tabs), 3)
    if told_none:
        out["false_none"] = True
    return out


def score_not_covered(q: dict, resp: dict) -> dict:
    cov = resp.get("coverage")
    if (cov == "none" or not resp.get("results") or resp.get("not_loaded") or resp.get("external_standards")
            or resp.get("found") is False):
        val = 1.0
    elif cov == "weak":
        val = 0.5
    else:
        val = 0.0
    return {"N": val, "score": val, "coverage": cov or "(no signal)"}


def score_revision(index: StandardsIndex, q: dict, resp: dict) -> dict:
    """The question names `asked_issue`, which is not the loaded issue of `doc_id`."""
    e = q["expected"][0]
    flagged = any(m.get("doc_id") == e["doc_id"] for m in resp.get("issue_mismatch") or [])
    g = tools.get_requirement(index, f"{e['doc_id']} {q['asked_issue']}".strip() if not q.get("asked_doc")
                              else q["asked_doc"], (e.get("req_ids") or [e.get("clause", "")])[0])
    # a silent answer from another issue is the failure; a refusal that names the loaded issue, or an answer
    # that carries the mismatch, is right
    explained = bool(g.get("issue_mismatch") or g.get("loaded_issues"))
    val = (flagged + explained) / 2
    return {"W": val, "score": val, "search_flag": flagged, "lookup_flag": explained}


def edition_complete(recs: list[dict]) -> tuple[int, int]:
    ok = sum(bool(r.get("doc_id") and r.get("req_id") and (r.get("issue") or r.get("issue_date"))) for r in recs)
    return ok, len(recs)


def run(index: StandardsIndex, questions: list[dict], k: int) -> dict:
    out = {}
    for q in questions:
        resp = tools.search_requirements(index, q["question"], limit=k)
        if q["type"] == "not_covered":
            res = score_not_covered(q, resp)
        elif q["type"] == "revision":
            res = score_revision(index, q, resp)
        else:
            res = score_covered(index, q, resp)
        if "S" in res and hasattr(tools, "find_standards"):  # diagnostic, not in the total: document ranking
            ranked = [d["doc_id"] for d in tools.find_standards(index, q["question"], limit=5).get("documents", [])]
            res["D"] = round(sum(e["doc_id"] in ranked for e in q["expected"]) / len(q["expected"]), 3)
        res["type"], res["area"] = q["type"], q.get("area", "")
        res["edition"] = edition_complete(_records(resp))
        out[q["id"]] = res
    return out


def summarise(scores: dict) -> dict:
    def mean(xs):
        xs = [x for x in xs if x is not None]
        return round(sum(xs) / len(xs), 3) if xs else None

    vals = list(scores.values())
    covered = [v for v in vals if "S" in v]
    ed_ok, ed_n = sum(v["edition"][0] for v in vals), sum(v["edition"][1] for v in vals)
    summary = {
        "total": round(100 * mean([v["score"] for v in vals]), 1),
        "questions": len(vals),
        "covered": {"n": len(covered), **{k: mean([v[k] for v in covered]) for k in "SCLR"},
                    "tables": mean([v.get("T") for v in covered]),
                    "find_standards_top5": mean([v.get("D") for v in covered]),
                    "false_none": sum(bool(v.get("false_none")) for v in covered)},
        "not_covered": {"n": sum(v["type"] == "not_covered" for v in vals),
                        "N": mean([v.get("N") for v in vals if v["type"] == "not_covered"])},
        "revision": {"n": sum(v["type"] == "revision" for v in vals),
                     "W": mean([v.get("W") for v in vals if v["type"] == "revision"])},
        "edition_complete": round(ed_ok / ed_n, 3) if ed_n else None,
    }
    by_area = defaultdict(list)
    for v in vals:
        by_area[v["area"]].append(v["score"])
    summary["by_area"] = {a: [round(100 * mean(x), 1), len(x)] for a, x in sorted(by_area.items())}
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--docs", default="documents")
    ap.add_argument("--questions", default=str(HERE / "coverage_questions.yaml"))
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--save", help="write per-question scores and the summary as JSON (text-free)")
    ap.add_argument("--compare", help="an earlier --save file: print the questions whose score changed")
    ap.add_argument("--quiet", action="store_true", help="summary only")
    args = ap.parse_args()

    catalogue = build_catalogue(Path(args.docs))
    index = StandardsIndex(catalogue.load_documents(), catalogue=catalogue)
    questions = yaml.safe_load(Path(args.questions).read_text(encoding="utf-8"))
    scores = run(index, questions, args.k)
    summary = summarise(scores)

    if not args.quiet:
        for qid, v in scores.items():
            if "S" in v:
                miss = [f"{d['doc_id']}:{','.join(map(str, d['lookup_miss']))}" for d in v["detail"] if d["lookup_miss"]]
                extra = f"S={v['S']:.2f} C={v['C']:.2f} L={v['L']:.2f} R={v['R']:.2f}" + (
                    f" T={v['T']:.2f}" if "T" in v else "") + (" FALSE-NONE" if v.get("false_none") else "") + (
                    f"  lookup miss: {miss}" if miss else "")
            elif v["type"] == "not_covered":
                extra = f"N={v['N']:.1f} coverage={v['coverage']}"
            else:
                extra = f"W={v['W']:.1f} search_flag={v['search_flag']} lookup_flag={v['lookup_flag']}"
            print(f"{qid:10} {v['type']:13} {v['score']:.2f}  {extra}")
        print()
    c = summary["covered"]
    print(f"TOTAL {summary['total']:.1f} / 100 over {summary['questions']} questions ({len(index.documents)} documents loaded)")
    print(f"  covered ({c['n']}): standard {c['S']}, clause {c['C']}, lookup {c['L']}, revision {c['R']}, "
          f"tables {c['tables']}, find_standards top-5 {c['find_standards_top5']}, false 'none' {c['false_none']}")
    print(f"  not covered ({summary['not_covered']['n']}): {summary['not_covered']['N']}   "
          f"revision traps ({summary['revision']['n']}): {summary['revision']['W']}   "
          f"edition complete: {summary['edition_complete']}")
    print("  by area: " + "; ".join(f"{a} {s} (n={n})" for a, (s, n) in summary["by_area"].items()))

    if args.compare:
        old = json.loads(Path(args.compare).read_text())
        print(f"\nvs {args.compare}: total {old['summary']['total']} -> {summary['total']}")
        for qid, v in scores.items():
            o = old["scores"].get(qid)
            if o is None:
                print(f"  {qid}: new ({v['score']:.2f})")
            elif abs(o["score"] - v["score"]) > 1e-9:
                print(f"  {qid}: {o['score']:.2f} -> {v['score']:.2f}")
    if args.save:
        Path(args.save).parent.mkdir(parents=True, exist_ok=True)
        slim = {qid: {k: v[k] for k in v if k != "edition"} for qid, v in scores.items()}
        Path(args.save).write_text(json.dumps({"summary": summary, "k": args.k, "scores": slim}, indent=1) + "\n")


if __name__ == "__main__":
    main()
