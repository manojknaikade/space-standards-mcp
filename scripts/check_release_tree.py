#!/usr/bin/env python3
"""CI guard (release plan C6): no standards files in the tracked tree.

Fails (exit 1, paths printed) when `git ls-files` lists a .pdf, .doc, .docx or .pkl file, or anything under
`documents/` except `documents/README.md`. Also fails when `scripts/release_exclude.txt` is missing or has a
pattern that matches no tracked file (a stale entry). When no entry matches a tracked file at all, the tree is
the release tree itself (D1a left those files out) and the `--release` checks run instead. Standard library only.

The release-exclude list names files that stay in the private development repository and are left out of the
public tree (release plan D1a, e.g. the round log docs/PROGRESS.md).

    python scripts/check_release_tree.py                   # CI guard (both repositories)
    python scripts/check_release_tree.py --release         # the release tree: no excluded file tracked, no
                                                           # markdown link into one (stale entries are fine)
    python scripts/check_release_tree.py --print-excluded  # tracked paths on the list, for `git rm --cached`
"""

from __future__ import annotations

import argparse
import fnmatch
import posixpath
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {".pdf", ".doc", ".docx", ".pkl"}
DOCUMENTS_KEEP = "documents/README.md"
EXCLUDE_FILE = ROOT / "scripts" / "release_exclude.txt"
LINK_RE = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+[^)]*)?\)")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def forbidden(paths: list[str]) -> list[str]:
    """The paths that must not be tracked, sorted."""
    out = []
    for p in paths:
        norm = p.replace("\\", "/").removeprefix("./")
        if Path(norm).suffix.lower() in FORBIDDEN_SUFFIXES or (
                norm.startswith("documents/") and norm != DOCUMENTS_KEEP):
            out.append(p)
    return sorted(out)


def load_excludes(path: Path = EXCLUDE_FILE) -> list[str]:
    """Patterns from the exclude file: one per line, `#` comments and blank lines ignored."""
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def _norm(p: str) -> str:
    return p.replace("\\", "/").removeprefix("./")


def _matches(path: str, patterns: list[str]) -> bool:
    norm = _norm(path)
    return any(fnmatch.fnmatchcase(norm, pat) for pat in patterns)


def excluded(paths: list[str], patterns: list[str]) -> list[str]:
    """The paths that match any exclude pattern, sorted."""
    return sorted(p for p in paths if _matches(p, patterns))


def stale_patterns(paths: list[str], patterns: list[str]) -> list[str]:
    """Patterns that match no path."""
    return [pat for pat in patterns if not excluded(paths, [pat])]


def excluded_links(md_path: str, text: str, patterns: list[str]) -> list[tuple[int, str]]:
    """(line, target) for each relative markdown link in `text` that points at an excluded path."""
    base = posixpath.dirname(_norm(md_path))
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for m in LINK_RE.finditer(line):
            target = m.group(1).split("#", 1)[0]
            if not target or target.startswith("/") or SCHEME_RE.match(target):
                continue
            resolved = posixpath.normpath(posixpath.join(base, target))
            if _matches(resolved, patterns):
                hits.append((n, m.group(1)))
    return hits


def tracked_files(root: Path = ROOT) -> list[str]:
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True)
    return [f for f in out.stdout.decode().split("\0") if f]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--release", action="store_true", help="check the release tree itself")
    mode.add_argument("--print-excluded", action="store_true", help="print tracked paths on the exclude list")
    args = ap.parse_args([] if argv is None else argv)

    files = tracked_files()
    if not EXCLUDE_FILE.is_file():
        print(f"Missing exclude list: {EXCLUDE_FILE.relative_to(ROOT)}", file=sys.stderr)
        return 1
    patterns = load_excludes()
    if args.print_excluded:
        for p in excluded(files, patterns):
            print(p)
        return 0

    # every entry stale: this is the public release tree, where the excluded files are gone by design
    release = args.release or bool(patterns) and not excluded(files, patterns)
    failed = False
    bad = forbidden(files)
    if bad:
        print("Standards files must not be committed (ADR-0002):", file=sys.stderr)
        for p in bad:
            print(f"  {p}", file=sys.stderr)
        failed = True
    if release:
        # In the release tree the excluded files are gone, so stale patterns are expected there.
        present = excluded(files, patterns)
        if present:
            print("Tracked files on the release-exclude list:", file=sys.stderr)
            for p in present:
                print(f"  {p}", file=sys.stderr)
            failed = True
        links = []
        for f in files:
            if not f.lower().endswith(".md") or not (ROOT / f).is_file():
                continue
            text = (ROOT / f).read_text(encoding="utf-8", errors="replace")
            links += [f"{f}:{n}: {t}" for n, t in excluded_links(f, text, patterns)]
        if links:
            print("Markdown links to release-excluded files:", file=sys.stderr)
            for entry in links:
                print(f"  {entry}", file=sys.stderr)
            failed = True
    else:
        stale = stale_patterns(files, patterns)
        if stale:
            print("Stale entries in scripts/release_exclude.txt (match no tracked file):", file=sys.stderr)
            for pat in stale:
                print(f"  {pat}", file=sys.stderr)
            failed = True
    if failed:
        return 1
    print("release tree ok: no .pdf/.doc/.docx/.pkl files, nothing under documents/ but its README"
          + ("; no excluded files or links to them" if release else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
