"""Answer evaluation: answer each question through the MCP tools, then score the answers.

    # 1. answers (Anthropic API with the tools in-process, or the `claude` CLI with the MCP server)
    python eval/run_answer_eval.py generate --run eval/runs/baseline --backend api   # needs ANTHROPIC_API_KEY
    python eval/run_answer_eval.py generate --run eval/runs/baseline --backend cli   # needs a logged-in `claude`
    python eval/run_answer_eval.py generate --run eval/runs/agent --backend agent    # api + citation gate (ADR-0005)
    python eval/run_answer_eval.py generate --run eval/runs/cli-agent --backend cli-agent  # cli + citation gate
    SPACESTD_EMBED=default python eval/run_answer_eval.py generate ...               # hybrid search (".[embed]")
    # 2. scores: deterministic checks, plus an LLM judge on the answer points
    python eval/run_answer_eval.py score --run eval/runs/baseline --judge api|cli|none

Answers can also come from any other client: put {id, answer} records in <run>/answers.jsonl.
eval/runs/ is gitignored: answers and tool results quote standards text (ADR-0002). Only the summary goes
to eval/RESULTS.md (`score --markdown`).

Deterministic checks (src/spacestd/citations.py), per answer:
- invented IDs: requirement or table IDs that exist in no loaded document;
- citation recall: expected_ids (and expected_tables) the answer cites;
- ungrounded numbers: numbers not found in the question or in the records/tables the answer cites;
- declines: says the loaded standards do not cover it (must, for not_covered questions).
LLM judge, per answer: each answer point yes / partial / no, factual errors against the reference, and a
verdict correct / partial / wrong.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from spacestd.citations import CitationChecker, norm_key
from spacestd.embeddings import index_options_from_env
from spacestd.index import StandardsIndex
from spacestd.loaders import load_folder
from spacestd_agent.agent import ANSWER_SYSTEM  # the agent's loop is the api backend's loop
from spacestd_agent.claude_code import SEARCH_ENV, ClaudeCode, ClaudeCodeAgent

HERE = Path(__file__).parent
DEFAULT_MODEL = "claude-sonnet-5-5"
JUDGE_SYSTEM = (
    "You grade answers to questions about space structures standards against a reference written by a "
    "domain expert. Judge content, not style. Reply with one JSON object only."
)
JUDGE_PROMPT = """Question ({qtype}):
{question}

Reference answer (paraphrase of the source; may be empty):
{reference}

Answer points the answer must contain:
{points}

Answer to grade:
<answer>
{answer}
</answer>

For each answer point, decide whether the answer states it: "yes", "partial" (incomplete or vague) or "no".
List factual errors: statements that contradict the reference or the points (wrong value, wrong condition,
claiming coverage the reference says is missing). Omissions are not errors.
Verdict: "correct" (all points yes, no errors), "partial" (some points missing or partial, no serious error),
or "wrong" (a serious error, e.g. a wrong number, or answering a question the loaded standards do not cover).

Reply as JSON: {{"points": [{{"point": "...", "grade": "yes|partial|no", "note": "..."}}], "errors": ["..."],
"verdict": "correct|partial|wrong"}}"""


# -- backends -----------------------------------------------------------------------------------------

class ApiBackend:
    """Anthropic Messages API with the MCP server's tools in-process: the agent's loop with the gate off."""

    gate = False

    def __init__(self, model: str, docs: Path):
        import anthropic  # optional dependency: pip install -e ".[eval]"

        from spacestd_agent import StandardsAgent

        self.model, self.client = model, anthropic.Anthropic()
        self.agent = StandardsAgent(StandardsIndex(load_folder(docs), **index_options_from_env()), self.client,
                                    model=model, gate=self.gate)

    def complete(self, system: str, prompt: str, max_tokens: int = 2000) -> str:
        msg = self.client.messages.create(model=self.model, max_tokens=max_tokens, system=system,
                                          messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in msg.content if b.type == "text")

    def answer(self, question: str) -> dict:
        return self.agent.ask(question).to_record()


class AgentBackend(ApiBackend):
    """The Phase 3 agent: the same loop with the citation gate (ADR-0005)."""

    gate = True


class CliBackend:
    """`claude -p` (Claude Code) with the space-standards MCP server: an off-the-shelf client."""

    def __init__(self, model: str, docs: Path):
        self.claude = ClaudeCode(model, docs)

    def complete(self, system: str, prompt: str, max_tokens: int = 2000) -> str:
        return self.claude.complete(system, prompt)

    def answer(self, question: str) -> dict:
        out = self.claude.answer(question)
        out.pop("session_id", None)
        return out


class CliAgentBackend(CliBackend):
    """The agent's citation gate around the same `claude -p` client (runs on a Claude Code login)."""

    def __init__(self, model: str, docs: Path):
        super().__init__(model, docs)
        self.agent = ClaudeCodeAgent(StandardsIndex(load_folder(docs), **index_options_from_env()), self.claude)

    def answer(self, question: str) -> dict:
        return self.agent.ask(question).to_record()




def make_backend(name: str, model: str, docs: Path):
    return {"api": ApiBackend, "agent": AgentBackend, "cli": CliBackend, "cli-agent": CliAgentBackend}[name](model, docs)


# -- generate -----------------------------------------------------------------------------------------

def load_questions(path: Path, ids: list[str] | None) -> list[dict]:
    qs = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [q for q in qs if not ids or q["id"] in ids]


def read_jsonl(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    recs = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {r["id"]: r for r in recs}


def generate(args) -> None:
    run = Path(args.run)
    run.mkdir(parents=True, exist_ok=True)
    out_path = run / "answers.jsonl"
    done = {k for k, r in read_jsonl(out_path).items() if r.get("answer") and not r.get("error")}
    todo = [q for q in load_questions(Path(args.questions), args.ids) if q["id"] not in done]
    backend = make_backend(args.backend, args.model, Path(args.docs))
    (run / "meta.json").write_text(json.dumps({"backend": args.backend, "model": args.model,
                                               "docs": str(Path(args.docs).resolve()),
                                               "search": {k: os.environ.get(k) for k in SEARCH_ENV},
                                               "system": ANSWER_SYSTEM}, indent=1))
    print(f"{len(done)} answered already, {len(todo)} to go ({args.backend}, {args.model})")

    def one(q):
        try:
            rec = backend.answer(q["question"])
        except Exception as e:  # keep going; the record is retried on the next run
            rec = {"answer": "", "error": str(e)}
        return {"id": q["id"], **rec}

    with ThreadPoolExecutor(args.workers) as pool, out_path.open("a", encoding="utf-8") as f:
        for rec in pool.map(one, todo):
            f.write(json.dumps(rec) + "\n")
            f.flush()
            status = f"ERROR {rec['error'][:80]}" if rec.get("error") else f"{len(rec.get('tool_calls', []))} tool calls"
            print(f"{rec['id']}: {status}")


# -- score --------------------------------------------------------------------------------------------

def parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"no JSON in judge reply: {text[:200]!r}")
    return json.loads(m.group(0))


def judge(backend, q: dict, answer: str) -> dict:
    prompt = JUDGE_PROMPT.format(
        qtype=q["type"], question=q["question"],
        reference=" ".join((q.get("reference_answer") or "").split()),
        points="\n".join(f"- {p}" for p in q["answer_points"]), answer=answer)
    res = parse_json(backend.complete(JUDGE_SYSTEM, prompt))
    grades = [p.get("grade") for p in res.get("points", [])]
    res["coverage"] = round(sum({"yes": 1, "partial": 0.5}.get(g, 0) for g in grades) / max(len(grades), 1), 3)
    return res


def check_one(checker: CitationChecker, q: dict, rec: dict) -> dict:
    chk = checker.check(rec["answer"], q["question"])
    cited = {norm_key(k) for k in chk.cited_keys}
    exp = [norm_key(e) for e in q.get("expected_ids") or []]
    tabs = [norm_key(e) for e in q.get("expected_tables") or []]
    out = {**chk.to_dict(),
           "citation_recall": round(sum(e in cited for e in exp) / len(exp), 3) if exp else None,
           "table_recall": round(sum(t in cited for t in tabs) / len(tabs), 3) if tabs else None}
    if q["type"] == "not_covered":
        out["not_covered_ok"] = chk.declines and not chk.ungrounded
    return out


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs), len(xs)) if xs else (None, 0)


def summarise(qs: list[dict], scores: dict[str, dict]) -> list[tuple[str, str, str]]:
    """Rows (metric, value, over n) for all questions, then the per-type answer verdicts."""
    s = [scores[q["id"]] for q in qs if q["id"] in scores]
    covered = [scores[q["id"]] for q in qs if q["id"] in scores and q["type"] != "not_covered"]
    nc = [scores[q["id"]] for q in qs if q["id"] in scores and q["type"] == "not_covered"]
    rows = []

    def add(name, xs, fmt="{:.2f}"):
        m, n = _mean(xs)
        rows.append((name, "—" if m is None else fmt.format(m), str(n)))

    judged = [x for x in s if "judge" in x]
    if judged:
        for v in ("correct", "partial", "wrong"):
            add(f"judge: {v}", [x["judge"]["verdict"] == v for x in judged])
        add("judge: answer-point coverage", [x["judge"]["coverage"] for x in judged])
    add("citation recall (expected IDs cited)", [x["citation_recall"] for x in covered])
    add("table citation recall", [x["table_recall"] for x in covered])
    add("answers with an invented ID", [bool(x["invented"]) for x in s])
    add("answers with an ungrounded number (covered)", [bool(x["ungrounded"]) for x in covered])
    add("not covered: declines, no numbers", [x["not_covered_ok"] for x in nc])
    add("covered: declines wrongly (cites nothing)", [x["declines"] and not x["cited"] for x in covered])
    add("tool calls per answer", [x.get("tool_calls") for x in s], "{:.1f}")
    gated = [x for x in s if x.get("gate")]
    if gated:
        for g in ("revised", "flagged", "declined"):
            add(f"agent gate: {g}", [x["gate"] == g for x in gated])
    return rows


def score(args) -> None:
    run = Path(args.run)
    run.mkdir(parents=True, exist_ok=True)
    answers = read_jsonl(Path(args.answers) if args.answers else run / "answers.jsonl")
    qs = [q for q in load_questions(Path(args.questions), args.ids) if q["id"] in answers]
    checker = CitationChecker(StandardsIndex(load_folder(Path(args.docs))))
    scores_path = run / "scores.json"
    old = json.loads(scores_path.read_text()) if scores_path.exists() else {}
    backend = make_backend(args.judge, args.judge_model, Path(args.docs)) if args.judge != "none" else None

    def one(q):
        rec = answers[q["id"]]
        res = {"type": q["type"], "tool_calls": len(rec.get("tool_calls", [])) if "tool_calls" in rec else None,
               **check_one(checker, q, rec)}
        if rec.get("gate"):
            res["gate"] = rec["gate"]["status"]
        if rec.get("error") or not rec.get("answer"):
            res["error"] = rec.get("error") or "empty answer"
        prev = old.get(q["id"], {})
        if prev.get("judge") and prev.get("answer_hash") == hash_text(rec["answer"]) and not args.rejudge:
            res["judge"] = prev["judge"]
        elif backend and rec.get("answer"):
            try:
                res["judge"] = judge(backend, q, rec["answer"])
            except Exception as e:
                res["judge_error"] = str(e)
        res["answer_hash"] = hash_text(rec["answer"])
        return q["id"], res

    with ThreadPoolExecutor(args.workers) as pool:
        scores = dict(pool.map(one, qs))
    scores_path.write_text(json.dumps(scores, indent=1))

    for q in qs:
        x = scores[q["id"]]
        verdict = x.get("judge", {}).get("verdict", "-")
        flags = []
        if x["invented"]:
            flags.append(f"invented={x['invented']}")
        if x["ungrounded"]:
            flags.append(f"ungrounded={x['ungrounded']}")
        if x["citation_recall"] is not None and x["citation_recall"] < 1:
            missing = [e for e in q["expected_ids"] if norm_key(e) not in {norm_key(k) for k in x["cited"]}]
            flags.append(f"not cited={missing}")
        if q["type"] == "not_covered" and not x["not_covered_ok"]:
            flags.append("did not decline cleanly")
        if x.get("error") or x.get("judge_error"):
            flags.append(f"error={x.get('error') or x.get('judge_error')}")
        print(f"{q['id']:8} {q['type']:14} {verdict:8} {'  '.join(flags)}")

    rows = summarise(qs, scores)
    print()
    width = max(len(r[0]) for r in rows)
    for name, val, n in rows:
        print(f"{name:{width}}  {val:>5}  (n={n})")
    by_type = defaultdict(list)
    for q in qs:
        if "judge" in scores[q["id"]]:
            by_type[q["type"]].append(scores[q["id"]]["judge"]["verdict"])
    if by_type:
        print("\nVerdicts by type: " + "; ".join(
            f"{t} {v.count('correct')}/{v.count('partial')}/{v.count('wrong')}" for t, v in sorted(by_type.items())))
    if args.markdown:
        print("\n| Metric | Value | n |\n| --- | --- | --- |")
        for name, val, n in rows:
            print(f"| {name} | {val} | {n} |")


def hash_text(text: str) -> str:
    import hashlib

    return hashlib.sha256((text or "").encode()).hexdigest()[:16]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("generate", "score"):
        p = sub.add_parser(name)
        p.add_argument("--run", required=True, help="run folder, e.g. eval/runs/baseline")
        p.add_argument("--docs", default="documents")
        p.add_argument("--questions", default=str(HERE / "questions.yaml"))
        p.add_argument("--ids", nargs="*", help="only these question IDs")
        p.add_argument("--workers", type=int, default=2)
    g = sub.choices["generate"]
    g.add_argument("--backend", choices=["api", "agent", "cli", "cli-agent"], default="api")
    g.add_argument("--model", default=DEFAULT_MODEL)
    s = sub.choices["score"]
    s.add_argument("--judge", choices=["api", "cli", "none"], default="api")
    s.add_argument("--judge-model", default=DEFAULT_MODEL)
    s.add_argument("--answers", help="answers file (JSONL of {id, answer}); default <run>/answers.jsonl")
    s.add_argument("--rejudge", action="store_true", help="judge again even if the answer is unchanged")
    s.add_argument("--markdown", action="store_true", help="also print the summary as a Markdown table")
    args = ap.parse_args()
    {"generate": generate, "score": score}[args.cmd](args)


if __name__ == "__main__":
    main()
