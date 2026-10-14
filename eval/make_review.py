"""Render eval/questions.yaml as a Markdown review sheet (eval/REVIEW.md).

Usage: python eval/make_review.py
Edit the YAML (review: ok | fix, review_note: ...), then re-run.
"""

from pathlib import Path

import yaml

HERE = Path(__file__).parent


def main() -> None:
    qs = yaml.safe_load((HERE / "questions.yaml").read_text(encoding="utf-8"))
    out = [
        "# Evaluation set — review sheet",
        "",
        "Generated from `questions.yaml` by `make_review.py`. Edit the YAML, not this file.",
        "",
        f"{len(qs)} questions · status: "
        + ", ".join(f"{s}: {sum(q.get('review') == s for q in qs)}" for s in ("pending", "ok", "fix")),
        "",
    ]
    for q in qs:
        out += [
            f"## {q['id']} · {q['type']} · review: {q.get('review', 'pending')}",
            "",
            f"**Q:** {q['question']}",
            "",
            *([f"**Answer:** {' '.join(q['reference_answer'].split())}", ""] if q.get("reference_answer") else []),
            "**Must contain:** " + "; ".join(q["answer_points"]),
            "",
            "**Sources:** " + (", ".join(f"`{e}`" for e in q["expected_ids"]) or "none (not covered)"),
            "",
        ]
        if q.get("kind_note"):
            out += [f"> Note: {q['kind_note']}", ""]
        if q.get("review_note"):
            out += [f"> Review: {q['review_note']}", ""]
    (HERE / "REVIEW.md").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {HERE / 'REVIEW.md'}")


if __name__ == "__main__":
    main()
