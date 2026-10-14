#!/usr/bin/env python
"""Write a hand-check list (B3) for the `checked` standards of the loaded set: for each one, the record counts
by kind, the first and last requirement IDs, spot-check IDs with their pages, records the parser flagged, and
every table with its page and shape. The owner checks them against the PDF; confirmed facts go into
tests/test_real_documents.py and catalogue.VERIFIED.

Text-free (ADR-0002): counts, IDs, page numbers and shapes only, never words from a standard.

    python scripts/hand_check_list.py [--docs documents] [--out eval/HAND_CHECK_WAVE1.md] [--spot 8]
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from spacestd.catalogue import build_catalogue
from spacestd.health import checked_tiers, ragged

KINDS = ("requirement", "recommendation", "permission", "guidance", "deleted")


def spot_ids(reqs, n: int) -> list:
    """First, last and evenly spaced requirements in between (deterministic)."""
    if len(reqs) <= n:
        return list(reqs)
    step = (len(reqs) - 1) / (n - 1)
    return [reqs[round(i * step)] for i in range(n)]


def section(doc, entry, n_spot: int) -> list[str]:
    reqs = [r for r in doc.requirements if r.kind == "requirement"]
    kinds = Counter(r.kind for r in doc.requirements)
    flagged = [r for r in doc.requirements if r.flags or "(duplicate" in r.req_id]
    out = [
        f"### {doc.doc_id} {doc.issue}".rstrip(),
        "",
        f"Source: `{entry.source}`. Records: {len(doc.requirements)} ("
        + ", ".join(f"{kinds.get(k, 0)} {k}" for k in KINDS) + ").",
        "",
        f"- [ ] Requirement count {len(reqs)} matches the PDF"
        + (f" (first `{reqs[0].req_id}` p. {reqs[0].page or '?'}, last `{reqs[-1].req_id}` p. {reqs[-1].page or '?'})"
           if reqs else ""),
        "- [ ] Spot checks (ID exists, text complete, kind right): "
        + ", ".join(f"`{r.req_id}` p. {r.page or '?'}" for r in spot_ids(reqs, n_spot)),
    ]
    by_flag: dict[str, list] = {}
    for r in flagged:
        for f in r.flags or ["duplicate ID"]:
            by_flag.setdefault(f.split(" '")[0], []).append(r)  # stale-reference flags carry a field name
    for flag, rs in sorted(by_flag.items(), key=lambda kv: -len(kv[1])):
        out.append(f"- [ ] Parser flag \"{flag}\" on {len(rs)} records, e.g. "
                   + ", ".join(f"`{r.req_id}` p. {r.page or '?'}" for r in spot_ids(rs, 4)))
    for t in doc.tables:
        ncols = len(t.value_columns)
        out.append(f"- [ ] {t.table_id} p. {t.page or '?'}: {len(t.rows)} rows × {ncols} value columns"
                   + (", ragged (check rows and merged cells)" if ragged(t) else "")
                   + (f", owner `{t.clause}`" if t.clause else "") + " — values match the PDF")
    out.append("")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--docs", default="documents")
    ap.add_argument("--out", default="eval/HAND_CHECK_WAVE1.md")
    ap.add_argument("--spot", type=int, default=8)
    args = ap.parse_args()
    folder = Path(args.docs)
    cat = build_catalogue(folder)
    tiers = checked_tiers(folder)
    entries = {(e.doc_id, e.issue): e for e in cat.entries}
    docs = [d for d in cat.load_documents()
            if tiers.get((d.doc_id, d.issue, entries[(d.doc_id, d.issue)].source)) == "checked"
            and entries[(d.doc_id, d.issue)].doc_type in ("standard", "specification")]
    lines = [
        "# Hand-check list, wave 1 (B3)",
        "",
        "Written by `python scripts/hand_check_list.py`. Text-free: IDs, counts, pages and table shapes only.",
        "Tick what matches the PDF; note what does not (ID and page, never the wording). Confirmed counts, IDs and",
        "table values go into `tests/test_real_documents.py`, and the standard into `catalogue.VERIFIED`.",
        f"Standards: {len(docs)} at tier `checked` (handbooks can stay `checked`).",
        "",
    ]
    for d in sorted(docs, key=lambda d: d.doc_id):
        lines += section(d, entries[(d.doc_id, d.issue)], args.spot)
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(docs)} standards -> {args.out}")


if __name__ == "__main__":
    main()
