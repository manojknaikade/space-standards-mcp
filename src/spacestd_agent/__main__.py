"""Ask the agent one question.

    python -m spacestd_agent "What ultimate factor applies ...?" --docs documents [--json]

Needs the optional dependency (pip install -e ".[agent]") and Anthropic API credentials.
Hybrid search: the same SPACESTD_EMBED / SPACESTD_RERANK variables as the server.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from spacestd.catalogue import build_catalogue
from spacestd.embeddings import index_options_from_env
from spacestd.index import StandardsIndex

from .agent import MODEL, StandardsAgent


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m spacestd_agent")
    ap.add_argument("question")
    ap.add_argument("--docs", default="documents")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--json", action="store_true", help="print the full record (gate findings, tool calls)")
    args = ap.parse_args()

    catalogue = build_catalogue(Path(args.docs))
    index = StandardsIndex(catalogue.load_documents(), catalogue=catalogue, **index_options_from_env())
    agent = StandardsAgent(index, model=args.model, effort=args.effort)
    res = agent.ask(args.question)
    if args.json:
        print(json.dumps({"question": res.question, "status": res.status, **res.to_record()}, indent=2,
                         ensure_ascii=False))
        return
    print(res.answer or f"(no answer: {res.error})")
    print(f"\n[gate: {res.status}; {len(res.tool_calls)} tool calls]")
    for p in res.problems:
        print(f"  first draft {p.lstrip('- ')}")
    if res.unretrieved:
        print(f"  cited but never retrieved: {', '.join(res.unretrieved)}")


if __name__ == "__main__":
    main()
