#!/usr/bin/env python3
"""Text audit (release plan C3): find standards text copied into the release tree.

Compares every file of the release tree (`git ls-files`, or a folder walk outside git) against the parsed
documents in `documents/`: requirement texts, notes, table captions, footnotes, table rows and unparsed
fragments. Reports

- every run of >= 12 consecutive words (`--min-words`) that also appears in a standard, and
- every table row copied whole (all its cells, in order, on one line of a file).

The report holds only file:line, the length of the match and the document / table ID it matches, never
the matched words (ADR-0002), so it can be committed or pasted. Exit code 1 when a hit is not in the
allowlist (`scripts/audit_allowlist.yaml`, the accepted hits of C4) or a document could not be parsed (listed:
its text was not compared). Allowlisted hits are listed as accepted.

    python scripts/audit_standards_text.py                      # documents/ vs this repository
    python scripts/audit_standards_text.py --docs documents --tree ../release --out audit.md

Words are compared case-blind, with typographic quotes and dashes folded and punctuation ignored, so a
copy that only changes line breaks, case or bullets still counts. Numbers from tables are facts and may
stay (release plan C4); sentences should be paraphrases.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_WORDS = 12
MIN_ROW_WORDS = 4  # shorter rows ("1 | 2") match by chance
MIN_ROW_FIELDS = 2
WORD_RE = re.compile(r"[^\W_]+")
FOLD = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "‐": "-", "‑": "-", "‒": "-", "–": "-",
                      "—": "-", "−": "-"})
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".spacestd-cache", "node_modules"}


def words(text: str) -> list[str]:
    return WORD_RE.findall(unicodedata.normalize("NFKC", text).translate(FOLD).lower())


# --- the release tree -------------------------------------------------------------------------------------

def tree_files(tree: Path) -> list[str]:
    """Tracked files (the release tree is one squashed commit of them); a folder walk outside git."""
    try:
        out = subprocess.run(["git", "-C", str(tree), "ls-files", "-z"], capture_output=True, check=True)
        files = [f for f in out.stdout.decode().split("\0") if f]
        if files:
            return sorted(files)
    except (OSError, subprocess.CalledProcessError):
        pass
    files = []
    for p in sorted(tree.rglob("*")):
        rel = p.relative_to(tree)
        if not p.is_file() or SKIP_DIRS & set(rel.parts) or rel.parts[:2] == ("eval", "runs"):
            continue
        if rel.parts[0] == "documents" and rel.as_posix() != "documents/README.md":
            continue
        files.append(rel.as_posix())
    return files


def read_text(path: Path) -> str | None:
    """File content, or None for binary / non-UTF-8 files (a PDF in the tree is CI's job, C6)."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


@dataclass
class TreeFile:
    path: str
    tokens: list[str] = field(default_factory=list)
    lines: list[int] = field(default_factory=list)  # 1-based line of each token
    line_tokens: dict[int, list[str]] = field(default_factory=dict)

    @classmethod
    def from_text(cls, path: str, text: str) -> TreeFile:
        f = cls(path)
        for n, line in enumerate(text.splitlines(), 1):
            ws = words(line)
            if ws:
                f.tokens += ws
                f.lines += [n] * len(ws)
                f.line_tokens[n] = ws
        return f


# --- the standards ----------------------------------------------------------------------------------------

def row_fields(row) -> list[str]:
    return [v for v in (*row.labels.values(), *(c.text for c in row.cells.values())) if v and v.strip()]


def segments(doc) -> list[str]:
    """Each piece of a parsed document's text. Runs are matched within a piece, not across two."""
    out = [doc.title]
    for r in doc.requirements:
        out += [r.text, *r.notes]
    for t in doc.tables:
        out += [t.caption, *t.footnotes.values(), *(" ".join(row_fields(row)) for row in t.rows)]
    out += doc.unparsed
    return [s for s in out if s]


@dataclass
class Hit:
    path: str
    line: int
    kind: str  # "words" or "table row"
    length: int  # words in the run, or fields in the row
    sources: set[str]

    def render(self) -> str:
        unit = "words" if self.kind == "words" else "fields, table row copied whole"
        return f"{self.path}:{self.line}  {self.length} {unit}  ({'; '.join(sorted(self.sources))})"


class Audit:
    def __init__(self, files: list[TreeFile], min_words: int = MIN_WORDS):
        self.files = files
        self.n = min_words
        self.windows: dict[tuple[str, ...], list[tuple[int, int]]] = defaultdict(list)  # gram -> (file, pos)
        for fi, f in enumerate(files):
            for i in range(len(f.tokens) - self.n + 1):
                self.windows[tuple(f.tokens[i:i + self.n])].append((fi, i))
        self.matched: dict[tuple[int, int], set[str]] = defaultdict(set)  # (file, pos) -> doc IDs
        self.lines_by_head: dict[tuple[str, ...], list[tuple[int, int, int]]] = defaultdict(list)
        for fi, f in enumerate(files):
            for line, ws in f.line_tokens.items():
                for i in range(len(ws) - MIN_ROW_WORDS + 1):
                    self.lines_by_head[tuple(ws[i:i + MIN_ROW_WORDS])].append((fi, line, i))
        self.rows: dict[tuple[int, int], tuple[int, set[str]]] = {}  # (file, line) -> (fields, table IDs)

    def add_document(self, doc) -> None:
        name = f"{doc.doc_id} {doc.issue}".strip()
        for seg in segments(doc):
            ws = words(seg)
            for i in range(len(ws) - self.n + 1):
                for where in self.windows.get(tuple(ws[i:i + self.n]), ()):
                    self.matched[where].add(name)
        for t in doc.tables:
            for row in t.rows:
                self._add_row(row, f"{name}, {t.table_id}")

    def _add_row(self, row, source: str) -> None:
        fields = row_fields(row)
        ws = words(" ".join(fields))
        if len(fields) < MIN_ROW_FIELDS or len(ws) < MIN_ROW_WORDS:
            return
        for fi, line, i in self.lines_by_head.get(tuple(ws[:MIN_ROW_WORDS]), ()):
            if self.files[fi].line_tokens[line][i:i + len(ws)] == ws:
                n, srcs = self.rows.get((fi, line), (0, set()))
                self.rows[(fi, line)] = (max(n, len(fields)), srcs | {source})

    def hits(self) -> list[Hit]:
        out = []
        by_file: dict[int, list[int]] = defaultdict(list)
        for fi, pos in self.matched:
            by_file[fi].append(pos)
        for fi, positions in by_file.items():  # overlapping windows -> one run
            positions.sort()
            start = prev = positions[0]
            for pos in [*positions[1:], None]:
                if pos is not None and pos == prev + 1:
                    prev = pos
                    continue
                f = self.files[fi]
                srcs = set().union(*(self.matched[(fi, p)] for p in range(start, prev + 1)))
                out.append(Hit(f.path, f.lines[start], "words", prev - start + self.n, srcs))
                if pos is not None:
                    start = prev = pos
        for (fi, line), (n, srcs) in self.rows.items():
            out.append(Hit(self.files[fi].path, line, "table row", n, srcs))
        return sorted(out, key=lambda h: (h.path, h.line, h.kind))


def load_allowlist(path: Path | None) -> list[dict]:
    """Entries {file, kind, length, source, reason}; a missing file is an empty allowlist."""
    if path is None or not path.is_file():
        return []
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def is_accepted(hit: Hit, allowlist: list[dict]) -> bool:
    """An entry matches on file and kind, on length when given, and when every source starts with its `source`
    (one prefix or a list of prefixes)."""
    for e in allowlist:
        if e.get("file") != hit.path or e.get("kind", hit.kind) != hit.kind:
            continue
        if "length" in e and e["length"] != hit.length:
            continue
        src = e.get("source", "")
        prefixes = tuple(str(x) for x in src) if isinstance(src, list) else (str(src),)
        if hit.sources and all(s.startswith(prefixes) for s in hit.sources):
            return True
    return False


def split_hits(hits: list[Hit], allowlist: list[dict]) -> tuple[list[Hit], list[Hit]]:
    """(new hits, accepted hits)."""
    accepted = [h for h in hits if is_accepted(h, allowlist)]
    return [h for h in hits if h not in accepted], accepted


def load_tree(tree: Path) -> tuple[list[TreeFile], int]:
    files, skipped = [], 0
    for rel in tree_files(tree):
        text = read_text(tree / rel)
        if text is None:
            skipped += 1
            continue
        files.append(TreeFile.from_text(rel, text))
    return files, skipped


def report(hits: list[Hit], n_files: int, skipped: int, n_docs: int, min_words: int,
           failed: list[str] = (), accepted: list[Hit] = ()) -> str:
    runs = sum(h.kind == "words" for h in hits)
    lines = [
        "# Text audit",
        "",
        f"{n_files} text files checked ({skipped} binary or non-UTF-8 skipped) against {n_docs} parsed documents.",
        f"{runs} runs of >= {min_words} words, {len(hits) - runs} table rows copied whole.",
        "Only locations, lengths and IDs are listed, never the matched text.",
        "",
    ]
    lines += [f"- {h.render()}" for h in hits]
    if accepted:  # decided in the allowlist; no exit code 1
        lines += ["", f"{len(accepted)} more hits accepted (scripts/audit_allowlist.yaml):", ""]
        lines += [f"- accepted: {h.render()}" for h in accepted]
    if failed:  # not audited: the result is incomplete
        lines += ["", f"{len(failed)} documents could not be parsed and were not compared:", ""]
        lines += [f"- {f}" for f in failed]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--docs", type=Path, default=ROOT / "documents", help="folder with the standards")
    ap.add_argument("--tree", type=Path, default=ROOT, help="release tree to audit (default: this repository)")
    ap.add_argument("--corpus", choices=["all", "loaded"], default="all",
                    help="every catalogued document, superseded ones included (default), or corpus.yaml's selection")
    ap.add_argument("--min-words", type=int, default=MIN_WORDS)
    ap.add_argument("--allowlist", type=Path, default=ROOT / "scripts" / "audit_allowlist.yaml",
                    help="accepted hits (default: scripts/audit_allowlist.yaml; none if the file is missing)")
    ap.add_argument("--no-cache", action="store_true", help="re-parse instead of using the parse cache")
    ap.add_argument("--out", type=Path, help="also write the report to this file")
    args = ap.parse_args(argv)

    from spacestd.catalogue import build_catalogue
    from spacestd.loaders import load_document

    if not args.docs.is_dir():
        ap.error(f"no documents folder at {args.docs}")
    files, skipped = load_tree(args.tree)
    audit = Audit(files, args.min_words)
    cat = build_catalogue(args.docs, not args.no_cache)
    entries = cat.loaded() if args.corpus == "loaded" else cat.entries
    failed = []
    for i, e in enumerate(entries, 1):
        try:
            doc = load_document(cat.folder / e.source, not args.no_cache,
                                {"doc_id": e.doc_id, "issue": e.issue, "title": e.title})
        except Exception as exc:  # noqa: BLE001 -- one broken file must not stop the audit; it is reported
            failed.append(f"{e.doc_id} {e.issue} ({type(exc).__name__})".replace("  ", " "))
            continue
        audit.add_document(doc)
        print(f"[{i}/{len(entries)}] {e.doc_id}", file=sys.stderr)
    hits, accepted = split_hits(audit.hits(), load_allowlist(args.allowlist))
    text = report(hits, len(files), skipped, len(entries) - len(failed), args.min_words, failed, accepted)
    print(text, end="")
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    return 1 if hits or failed else 0


if __name__ == "__main__":
    sys.exit(main())
