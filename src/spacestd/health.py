"""Parse health report: parse each catalogued document and check the result automatically (ADR-0006).

For every document: records by kind, share of records whose ID is valid for its family, duplicate IDs,
unparsed body fragments, coverage (words in records and unparsed fragments / words of the body text layer:
text that becomes neither is invisible otherwise, H6), tables and tables with ragged rows, whether the file
name names the same standard as the identity the catalogue gave it, parse time and errors. Thresholds (`THRESHOLDS`) give the
`checked` / `unchecked` tier; a `verified` document keeps its tier and is still reported.

Output is text-free (counts, IDs, scores; never a sentence from a standard): `eval/CORPUS_HEALTH.md` for
committing, and `health.json` in the parse cache folder, which the catalogue reads to mark documents
`checked`. A parser change invalidates it (the parse-code hash is stored with it).

    python -m spacestd.health documents [--corpus all] [--out eval/CORPUS_HEALTH.md] [--no-cache]
"""

from __future__ import annotations

import json
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .loaders import CACHE_DIR, _code_version, load_document, meta_from_text
from .models import Document

HEALTH_FILE = "health.json"
DEFAULT_OUT = Path("eval/CORPUS_HEALTH.md")

# A document is `checked` when it meets every threshold. Tuned on the A2 run (docs/PARSING_NOTES.md, H4).
THRESHOLDS = {
    "min_records": 20,  # ECSS / NASA standards: fewer records means the parser missed the body
    "min_records_other": 3,  # handbooks and other types (handbook section records come with A5)
    "min_valid_id_share": 0.95,  # records whose ID has the form its family uses
    # unparsed fragments / (records + unparsed fragments); not applied to ECSS standards, whose descriptive
    # prose paragraphs are fragments by design (H6): coverage gates those (wave-1 re-run, 10 Oct)
    "max_unparsed_share": 0.10,
    # words in records + unparsed / body words (PDF and Word; H6). Wave-1 re-run 10 Oct: standards 78-99 %
    "min_coverage": 0.75,
    "max_ragged_table_share": 0.10,  # tables with at least one ragged row / tables ...
    "max_ragged_tables": 1,  # ... unless there are no more ragged tables than this
}
ADOPTION_NOTICE = "adoption notice"  # adopts another standard; few or no records by nature, not a parse fault

# Requirement IDs the parsers produce, per family (ecss_parser, nasa_parser, parser).
ECSS_REQ_RE = re.compile(r"^(?:[A-Z]\.)?\d+(?:\.\d+)*(?:<[\d.]+>)?([a-z])\1?$")  # 4.3.1a, A.2.1<5.2>b, 5.1aa
NASA_REQ_RE = re.compile(r"^(?:(?:[A-Z]{2,6}|[A-Z]{1,5}\d) \d{1,4}(?: / \d+(?:\.\d+)*(?:\.[a-z])?)?"  # FSR 24, V2 6001,
                         # FCR 11 / 7.2.1.a; tagless: 4.2a, 4.3(1), 4.4 req 1
                         r"|\d+(?:\.\d+)*(?:[a-z]|\(\d{1,2}\)| req \d+)|\d+(?:\.\d+)+"  # 4.3.1 (numbered paragraph)
                         r"|\d+(?:\.\d+)* guidance \d+)$")  # 4.1.1 guidance 3
# handbook section records (A5): kind guidance, ID = the clause number (4.2.1, A.2.1, or an annex letter)
SECTION_ID_RE = re.compile(r"^(?:[A-Z]|(?:[A-Z]\.)?\d+(?:\.\d+)*)$")
GLOSSARY_ID_RE = re.compile(r"^\d+:\S.*$")  # glossary term records (H8): 1:Fibre
TAG_REQ_RE = re.compile(r"^[A-Z]{2,8}[- ]?\d{1,4}$")  # generic parser: [SWE-033] -> SWE-033
VALID_ID = {
    "ECSS": [ECSS_REQ_RE],
    "NASA": [NASA_REQ_RE],
    "other": [ECSS_REQ_RE, TAG_REQ_RE],
}


def valid_id(req_id: str, family: str) -> bool:
    return any(p.match(req_id) for p in VALID_ID.get(family, VALID_ID["other"]))


@dataclass
class Health:
    doc_id: str
    issue: str
    source: str
    family: str
    doc_type: str
    tier: str = "unchecked"  # verified | checked | unchecked
    records: int = 0
    by_kind: dict[str, int] = field(default_factory=dict)
    valid_ids: int = 0
    duplicate_ids: int = 0
    unparsed: int = 0
    body_words: int = 0  # 0 = not measured (text and Markdown files)
    covered_words: int = 0  # words in record texts and notes plus unparsed fragments
    tables: int = 0
    ragged_tables: int = 0
    name_id: str = "match"  # match | differs | none (no ID in the file name) | sidecar
    seconds: float = 0.0
    error: str = ""  # exception class only (a message could quote the document)
    reasons: list[str] = field(default_factory=list)  # why the document is not `checked`

    @property
    def valid_id_share(self) -> float:
        return self.valid_ids / self.records if self.records else 0.0

    @property
    def unparsed_share(self) -> float:
        total = self.records + self.unparsed
        return self.unparsed / total if total else 0.0

    @property
    def coverage(self) -> float:
        return min(self.covered_words / self.body_words, 1.0) if self.body_words else 0.0

    @property
    def ragged_table_share(self) -> float:
        return self.ragged_tables / self.tables if self.tables else 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["valid_id_share"] = round(self.valid_id_share, 3)
        d["coverage"] = round(self.coverage, 3)
        return d


def ragged(table) -> bool:
    """A row lacks a value column, has one the header does not name, or has no label at all."""
    cols = set(table.value_columns)
    return any(set(row.cells) != cols or (table.label_columns and not any(v.strip() for v in row.labels.values()))
               for row in table.rows)


REV_LETTER_RE = re.compile(r"(?<=\d)[A-Z]$")  # a revision letter ends the number (or the part: "Part 1A")


def base_number(doc_id: str) -> str:
    """Family, type and number of a standard without its revision letter or dots:
    NASA-STD-8799.1A -> NASA-STD-87991, ECSS-E-HB-32-20 Part 1A -> ECSS-E-HB-32-20 PART 1."""
    return REV_LETTER_RE.sub("", doc_id.upper()).replace(".", "")


def name_check(source: str, doc_id: str) -> str:
    """`differs` only when the file name names a different base number (H3): file names often drop the
    revision letter or the dot, or append a version ("1234Ver-40" reads as revision V)."""
    path = Path(source)
    if path.with_name(path.stem + ".meta.yaml").exists():
        return "sidecar"
    name_id = meta_from_text(path.stem)[0]
    if not name_id:
        return "none"
    return "match" if base_number(name_id) == base_number(doc_id) else "differs"


def measure(doc: Document, family: str) -> dict:
    """Counts for one parsed document (no thresholds applied)."""
    ids = [r.req_id for r in doc.requirements]
    return {
        "records": len(ids),
        "by_kind": dict(sorted(Counter(r.kind for r in doc.requirements).items())),
        "valid_ids": sum(valid_id(r.req_id, family) or (r.kind == "guidance" and bool(SECTION_ID_RE.match(r.req_id) or GLOSSARY_ID_RE.match(r.req_id)))
                         for r in doc.requirements),
        "duplicate_ids": sum("(duplicate" in i for i in ids),
        "unparsed": len(doc.unparsed),
        "body_words": doc.body_words,
        "covered_words": sum(len(w.split()) for r in doc.requirements for w in (r.text, *r.notes)) + doc.unparsed_words,
        "tables": len(doc.tables),
        "ragged_tables": sum(ragged(t) for t in doc.tables),
    }


def judge(h: Health) -> list[str]:
    """Reasons the document misses `checked`; empty when it passes."""
    t = THRESHOLDS
    reasons = []
    if h.error:
        return [f"parse error ({h.error})"]
    if h.doc_type == ADOPTION_NOTICE:
        return [ADOPTION_NOTICE]
    min_records = t["min_records"] if h.doc_type == "standard" else t["min_records_other"]
    if h.records < min_records:
        reasons.append(f"{h.records} records < {min_records}")
    if h.records and h.valid_id_share < t["min_valid_id_share"]:
        reasons.append(f"valid IDs {h.valid_id_share:.0%} < {t['min_valid_id_share']:.0%}")
    if h.unparsed_share > t["max_unparsed_share"] and not (h.family == "ECSS" and h.doc_type == "standard"):
        reasons.append(f"unparsed {h.unparsed_share:.0%} > {t['max_unparsed_share']:.0%}")
    if h.body_words and h.coverage < t["min_coverage"]:
        reasons.append(f"coverage {h.coverage:.0%} < {t['min_coverage']:.0%}")
    if h.ragged_tables > t["max_ragged_tables"] and h.ragged_table_share > t["max_ragged_table_share"]:
        reasons.append(f"ragged tables {h.ragged_tables}/{h.tables}")
    if h.name_id == "differs":
        reasons.append("file name names another standard")
    return reasons


def check_entry(folder: Path, entry, use_cache: bool = True) -> Health:
    h = Health(entry.doc_id, entry.issue, entry.source, entry.family, entry.doc_type,
               name_id=name_check(str(folder / entry.source), entry.doc_id))
    if not entry.identified:
        h.name_id = "none"
    start = time.perf_counter()
    try:
        doc = load_document(folder / entry.source, use_cache,
                            {"doc_id": entry.doc_id, "issue": entry.issue, "title": entry.title})
    except Exception as exc:  # one broken file must not stop a 285-document run
        h.error = type(exc).__name__
    else:
        for k, v in measure(doc, entry.family).items():
            setattr(h, k, v)
    h.seconds = round(time.perf_counter() - start, 2)
    h.reasons = judge(h)
    if not entry.identified:
        h.reasons.append("no standard number found")
    h.tier = "verified" if entry.tier == "verified" else ("checked" if not h.reasons else "unchecked")
    return h


def run(folder: Path, corpus: str = "loaded", use_cache: bool = True, progress=None) -> list[Health]:
    """Health of the loaded documents (`corpus="loaded"`) or of every active one (`"all"`)."""
    from .catalogue import build_catalogue

    cat = build_catalogue(Path(folder), use_cache)
    entries = cat.loaded() if corpus == "loaded" else [e for e in cat.entries if e.status == "active"]
    out = []
    for i, e in enumerate(sorted(entries, key=lambda e: e.doc_id), 1):
        out.append(check_entry(cat.folder, e, use_cache))
        if progress:
            progress(i, len(entries), out[-1])
    return out


def write_json(folder: Path, results: list[Health], corpus: str) -> Path:
    """Results of earlier runs by the same parser are kept for the documents this run did not parse."""
    path = Path(folder) / CACHE_DIR / HEALTH_FILE
    docs = {(h.doc_id, h.issue, h.source): h.to_dict() for h in results}
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
        if old.get("parser_version") == _code_version():
            for d in old.get("documents", []):
                docs.setdefault((d["doc_id"], d["issue"], d["source"]), d)
    except (OSError, ValueError, KeyError):
        pass
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"parser_version": _code_version(), "corpus": corpus, "thresholds": THRESHOLDS,
                                "documents": sorted(docs.values(), key=lambda d: d["doc_id"])}, indent=1),
                    encoding="utf-8")
    return path


def checked_tiers(folder: Path) -> dict[tuple[str, str, str], str]:
    """(doc_id, issue, source) -> tier, from a health.json written by the current parser; else empty."""
    path = Path(folder) / CACHE_DIR / HEALTH_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if data.get("parser_version") != _code_version():
        return {}
    return {(d["doc_id"], d["issue"], d["source"]): d["tier"] for d in data.get("documents", [])}


def _pct(x: float) -> str:
    return f"{x:.0%}"


def render(results: list[Health], corpus: str) -> str:
    tiers = Counter(h.tier for h in results)
    reasons = Counter(r.split(" (")[0] if r.startswith("parse error") else re.sub(r"[\d/%]+", "N", r)
                      for h in results for r in h.reasons)
    t = THRESHOLDS
    lines = [
        "# Corpus parse health",
        "",
        "Written by `python -m spacestd.health` (A1/A2 in docs/PUBLIC_RELEASE_PLAN.md). Text-free: counts, IDs",
        "and scores only. A document is `checked` when it meets every threshold; `verified` documents are",
        "hand-checked (tests/test_real_documents.py) and keep that tier.",
        "",
        f"- Corpus: `{corpus}`; {len(results)} documents: "
        + ", ".join(f"{tiers.get(k, 0)} {k}" for k in ("verified", "checked", "unchecked")),
        f"- Parse errors: {sum(bool(h.error) for h in results)}; parse time {sum(h.seconds for h in results):.0f} s",
        f"- Thresholds: at least {t['min_records']} records for a standard ({t['min_records_other']} for other "
        f"types), valid IDs ≥ {_pct(t['min_valid_id_share'])}, unparsed ≤ {_pct(t['max_unparsed_share'])} "
        "(not for ECSS standards), "
        f"coverage ≥ {_pct(t['min_coverage'])} (words in records and unparsed fragments / body words), "
        f"ragged tables ≤ {_pct(t['max_ragged_table_share'])} or ≤ {t['max_ragged_tables']}, file name names the "
        "same base number (or no standard, or a sidecar sets the identity); adoption notices are listed, not judged",
        f"- Parser version: `{_code_version()}`",
    ]
    if reasons:
        lines += ["", "Why documents are not `checked`:", ""]
        lines += [f"- {n} × {r}" for r, n in reasons.most_common()]
    lines += [
        "",
        "| Document | Issue | Tier | Records | Kinds (req/rec/perm/guid/del) | Valid IDs | Dup | Unparsed "
        "| Coverage | Tables (ragged) | Name ID | Time s | Reasons |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for h in results:
        k = h.by_kind
        kinds = "/".join(str(k.get(x, 0)) for x in ("requirement", "recommendation", "permission", "guidance",
                                                     "deleted"))
        lines.append(
            f"| {h.doc_id} | {h.issue} | {h.tier} | {h.records} | {kinds} | {_pct(h.valid_id_share)} "
            f"| {h.duplicate_ids} | {h.unparsed} | {_pct(h.coverage) if h.body_words else '–'} | {h.tables} ({h.ragged_tables}) | {h.name_id} | {h.seconds:.1f} "
            f"| {'; '.join(h.reasons)} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(prog="python -m spacestd.health", description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", nargs="?", default="documents")
    ap.add_argument("--corpus", choices=["loaded", "all"], default="loaded",
                    help="the documents corpus.yaml loads (default) or every active catalogued document")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Markdown report (default {DEFAULT_OUT})")
    ap.add_argument("--no-cache", action="store_true", help="re-parse every document (true parse times)")
    args = ap.parse_args()

    def progress(i: int, n: int, h: Health) -> None:
        print(f"[{i}/{n}] {h.doc_id}: {h.tier} ({h.records} records, {h.seconds:.1f} s)", flush=True)

    results = run(Path(args.folder), args.corpus, not args.no_cache, progress)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(results, args.corpus), encoding="utf-8")
    path = write_json(Path(args.folder), results, args.corpus)
    tiers = Counter(h.tier for h in results)
    print(f"\n{len(results)} documents: {dict(tiers)}; wrote {args.out} and {path}")


if __name__ == "__main__":
    main()
