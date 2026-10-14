"""Catalogue of every standard under the documents folder, loaded or not (ADR-0006).

Discovery is recursive. Each file is identified the way a loaded document is (`loaders.read_meta`: sidecar,
Word page header, cover page, file name) and files are grouped by doc_id: one source per document, the
others kept as alternates. Within a group, files nearer the top of the folder win (a file placed by hand
beats a copy in a downloaded bundle), then PDF over Word. Family, type and discipline follow from the doc
ID; titles come from the cover page or from a download manifest in the same folder (`loaders.manifest_record`).

`corpus.yaml` in the documents folder selects which catalogued documents are loaded:

    load:              # doc ID patterns (fnmatch, case-insensitive); "*" loads every active document
      - ECSS-E-ST-32*
      - NASA-STD-5001*

Without it, only files directly in the documents folder are loaded (the behaviour before the catalogue).
Files under a folder whose name starts with "superseded" are catalogued as superseded and never loaded.
Identities are cached in `.spacestd-cache/catalogue.json`, so a rescan only reads new or changed files.

    python -m spacestd.catalogue documents [--json]
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from .health import checked_tiers
from .loaders import CACHE_DIR, PREFERENCE, SUPPORTED, load_document, manifest_record, meta_from_text, read_meta
from .models import Document

CORPUS_FILE = "corpus.yaml"
CATALOGUE_CACHE = "catalogue.json"

# Documents with per-document parsing tests (tests/test_real_documents.py), hand-checked against the
# source: requirement counts, spot-checked IDs and every table value. Keyed by (doc_id, issue): another
# issue of the same standard is not verified.
VERIFIED = {
    ("ECSS-E-ST-32C", "Rev.1"),
    ("ECSS-E-ST-32-01C", "Rev.2"),
    ("ECSS-E-ST-32-08C", "Rev.1"),
    ("ECSS-E-ST-32-10C", "Rev.2 Corr.1"),
    ("ECSS-E-ST-32-03C", ""),  # B3, 10 Oct 2026 (after the round-3 parser fixes)
    ("ECSS-E-ST-32-11C", ""),  # B3, 10 Oct 2026
    ("ECSS-Q-ST-70C", "Rev.2"),
    ("NASA-STD-5001B", "w/Change 3"),
    ("NASA-STD-5019A", "w/Change 4"),
    # B3, 10 Oct 2026 (after the round-3 parser fixes)
    ("NASA-SPEC-5022", "w/Change 2"),
    ("NASA-STD-5002B", ""),
    ("NASA-STD-5005D", "w/Change 2"),
    ("NASA-STD-5006A", "w/Change 2"),
    ("NASA-STD-5018", "w/Change 1"),
    ("NASA-STD-5023", ""),
    # B3 round 4, 11 Oct 2026 (after the H16/H17 table fixes and the NASA italic/subscript fixes)
    ("ECSS-E-ST-32-02C", "Rev.1"),
    ("ECSS-E-ST-33-01C", "Rev.2"),
    ("NASA-STD-5008B", "w/Change 2"),
    ("NASA-STD-5009C", ""),
    ("NASA-STD-5012C", ""),
    ("NASA-STD-5017B", ""),
    ("NASA-STD-7001C", ""),
    ("NASA-STD-7003A", ""),
    # B3 round 5, 12 Oct 2026 (after the H18 / H19 table fixes)
    ("ECSS-E-ST-10-03C", "Rev.1"),
    ("NASA-STD-5020B", ""),
    ("NASA-STD-7002B", "w/Change 1"),
}

ECSS_TYPES = {"ST": "standard", "HB": "handbook", "AS": "adoption notice", "TM": "technical memorandum"}
NASA_TYPES = {"STD": "standard", "HDBK": "handbook", "SPEC": "specification"}

# ECSS branch + discipline number ("E-32"); the decade ("E-30") is the fallback.
ECSS_DISCIPLINES = {
    "E-10": "system engineering",
    "E-20": "electrical and optical engineering",
    "E-30": "mechanical engineering",
    "E-31": "thermal control",
    "E-32": "structures",
    "E-33": "mechanisms",
    "E-34": "environmental control and life support",
    "E-35": "propulsion",
    "E-40": "software engineering",
    "E-50": "communications",
    "E-60": "control engineering",
    "E-70": "ground systems and operations",
    "Q-10": "product assurance management",
    "Q-20": "quality assurance",
    "Q-30": "dependability",
    "Q-40": "safety",
    "Q-60": "EEE components",
    "Q-70": "materials, mechanical parts and processes",
    "Q-80": "software product assurance",
    "M-10": "project planning and implementation",
    "M-40": "configuration and information management",
    "M-60": "cost and schedule management",
    "M-70": "integrated logistic support",
    "M-80": "risk management",
    "E-80": "security",
    "U-00": "space sustainability",
    "S-00": "system",
    "P-00": "ECSS policy and organisation",
}
# NASA technical standards are numbered by discipline series; a coarse grouping, the title says more.
NASA_SERIES = {
    "1000": "systems engineering and integration",
    "2000": "information technology and software",
    "3000": "human factors and health",
    "4000": "electrical and avionics",
    "5000": "structures and mechanical",
    "6000": "materials and processes",
    "7000": "test, analysis and environments",
    "8700": "safety and mission assurance",
}

ECSS_ID_RE = re.compile(r"^ECSS-([A-Z])-(?:(ST|HB|AS|TM)-)?(\d{2})", re.I)
NASA_ID_RE = re.compile(r"^NASA-(STD|HDBK|SPEC)-(\d{4})", re.I)


def classify(doc_id: str) -> dict:
    """family, doc_type and discipline of a standard, from its number alone."""
    if m := ECSS_ID_RE.match(doc_id):
        branch, kind, num = m.group(1).upper(), (m.group(2) or "ST").upper(), m.group(3)
        key = f"{branch}-{num}"
        name = ECSS_DISCIPLINES.get(key) or ECSS_DISCIPLINES.get(f"{branch}-{num[0]}0") \
            or ECSS_DISCIPLINES.get(f"{branch}-00", "")
        return {"family": "ECSS", "doc_type": ECSS_TYPES[kind], "discipline": key, "discipline_name": name}
    if m := NASA_ID_RE.match(doc_id):
        kind, num = m.group(1).upper(), m.group(2)
        series = "8700" if num.startswith("87") else num[0] + "000"
        return {"family": "NASA", "doc_type": NASA_TYPES[kind], "discipline": f"NASA-{series}",
                "discipline_name": NASA_SERIES.get(series, "")}
    return {"family": "other", "doc_type": "", "discipline": "", "discipline_name": ""}


@dataclass
class Entry:
    doc_id: str
    issue: str
    title: str
    family: str
    doc_type: str
    discipline: str
    discipline_name: str
    source: str  # path relative to the documents folder
    status: str = "active"  # active | superseded
    tier: str = "unchecked"  # verified | checked (passes the health report, health.py) | unchecked (ADR-0006)
    loaded: bool = False
    date: str = ""  # from a download manifest, when there is one
    alternates: list[str] = field(default_factory=list)  # other files with the same doc_id
    alternate_issues: list[str] = field(default_factory=list)  # their issues, when different from `issue`
    identified: bool = True  # False: no standard number found, doc_id is the file name

    def to_dict(self, full: bool = False) -> dict:
        d = asdict(self)
        if not full:
            for k in ("alternates", "alternate_issues", "date"):
                if not d[k]:
                    d.pop(k)
            if d["identified"]:
                d.pop("identified")
        return d


@dataclass
class Catalogue:
    folder: Path
    entries: list[Entry]
    selection: list[str] | None  # corpus.yaml `load` patterns; None = top-level files only
    skipped: list[str] = field(default_factory=list)  # files found but not catalogued (unsupported type)

    def get(self, doc_id: str) -> Entry | None:
        return next((e for e in self.entries if e.doc_id == doc_id), None)

    def loaded(self) -> list[Entry]:
        return [e for e in self.entries if e.loaded]

    def load_documents(self, use_cache: bool = True) -> list[Document]:
        return [load_document(self.folder / e.source, use_cache, {"doc_id": e.doc_id, "issue": e.issue, "title": e.title})
                for e in sorted(self.loaded(), key=lambda e: e.source)]

    def summary(self) -> dict:
        active = [e for e in self.entries if e.status == "active"]
        return {
            "documents": len(self.entries),
            "active": len(active),
            "superseded": len(self.entries) - len(active),
            "loaded": len(self.loaded()),
            "by_family_type": dict(sorted(Counter(f"{e.family} {e.doc_type}" for e in active).items())),
            "by_discipline": dict(sorted(Counter(f"{e.discipline} {e.discipline_name}".strip()
                                                  for e in active).items())),
            "verified": sorted(e.doc_id for e in self.entries if e.tier == "verified"),
            "unidentified": sorted(e.source for e in self.entries if not e.identified),
            "issue_conflicts": {e.doc_id: [e.issue, *e.alternate_issues] for e in self.entries if e.alternate_issues},
            "selection": self.selection,
            "skipped_files": len(self.skipped),
        }


def _discover(folder: Path) -> list[Path]:
    out = []
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder)
        if any(part.startswith(".") for part in rel.parts) or not p.is_file():
            continue
        if p.suffix.lower() in SUPPORTED and p.name.lower() != "readme.md":
            out.append(p)
    return out


def _code_version() -> str:
    h = hashlib.sha1()
    for name in ("loaders", "catalogue"):
        h.update((Path(__file__).parent / f"{name}.py").read_bytes())
    return h.hexdigest()[:12]


def _identities(folder: Path, files: list[Path], use_cache: bool) -> dict[str, dict]:
    """relative path -> {doc_id, issue, title?}, cached by size and mtime.

    Copies of one download in several formats (same file name, any folder) share the identity read from
    the preferred format: a Word page header with a typo cannot split a PDF/Word pair into two documents.
    """
    cache_path = folder / CACHE_DIR / CATALOGUE_CACHE
    version = _code_version()
    cached: dict = {}
    if use_cache and cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            cached = data["files"] if data.get("version") == version else {}
        except (OSError, ValueError, KeyError):
            cached = {}
    stems: dict[str, list[Path]] = {}
    for p in files:
        stems.setdefault(p.stem.lower(), []).append(p)
    out, changed = {}, False
    for group in stems.values():
        p = min(group, key=lambda f: PREFERENCE[f.suffix.lower()])
        rel = p.relative_to(folder).as_posix()
        st = p.stat()
        stamp = f"{st.st_size}|{st.st_mtime_ns}"
        sidecar = p.with_name(p.stem + ".meta.yaml")
        if sidecar.exists():
            stamp += f"|{sidecar.stat().st_mtime_ns}"
        hit = cached.get(rel)
        if hit and hit.get("stamp") == stamp:
            meta = hit["meta"]
        else:
            meta = {k: str(v) for k, v in read_meta(p).items() if k in ("doc_id", "issue", "title")}
            cached[rel] = {"stamp": stamp, "meta": meta}
            changed = True
        for f in group:
            out[f.relative_to(folder).as_posix()] = meta
    if use_cache and changed and any(p.suffix.lower() in {".pdf", ".doc", ".docx"} for p in files):
        try:
            cache_path.parent.mkdir(exist_ok=True)
            keep = {k: v for k, v in cached.items() if k in out}
            cache_path.write_text(json.dumps({"version": version, "files": keep}, indent=1), encoding="utf-8")
        except OSError:
            pass
    return out


def _selection(folder: Path) -> list[str] | None:
    path = folder / CORPUS_FILE
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    load = data.get("load", [])
    return [load] if isinstance(load, str) else [str(x) for x in load]


def _selected(doc_id: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(doc_id.upper(), p.upper()) for p in patterns)


def build_catalogue(folder: Path, use_cache: bool = True) -> Catalogue:
    folder = Path(folder)
    files = _discover(folder)
    idents = _identities(folder, files, use_cache)
    selection = _selection(folder)
    health = checked_tiers(folder)

    def rank(p: Path) -> tuple:
        rel = p.relative_to(folder)
        superseded = any(part.lower().startswith("superseded") for part in rel.parts[:-1])
        return (superseded, len(rel.parts), PREFERENCE[p.suffix.lower()], rel.as_posix())

    groups: dict[str, list[Path]] = {}
    for p in files:
        groups.setdefault(idents[p.relative_to(folder).as_posix()]["doc_id"], []).append(p)

    entries = []
    for doc_id, paths in groups.items():
        paths.sort(key=rank)
        best = paths[0]
        rel = best.relative_to(folder)
        meta = idents[rel.as_posix()]
        superseded = rank(best)[0]
        manifest = next((r for r in map(manifest_record, paths) if r), {})
        title = meta.get("title") or next((idents[p.relative_to(folder).as_posix()].get("title")
                                           for p in paths if idents[p.relative_to(folder).as_posix()].get("title")),
                                          "") or manifest.get("title", "")
        alt_issues = sorted({idents[p.relative_to(folder).as_posix()].get("issue", "") for p in paths[1:]}
                            - {meta.get("issue", "")})
        if selection is None:
            loaded = len(rel.parts) == 1
        else:
            loaded = not superseded and _selected(doc_id, selection)
        e = Entry(
            doc_id=doc_id,
            issue=meta.get("issue", ""),
            title=" ".join(title.split()),
            source=rel.as_posix(),
            status="superseded" if superseded else "active",
            loaded=loaded,
            date=manifest.get("date", ""),
            alternates=[p.relative_to(folder).as_posix() for p in paths[1:]],
            alternate_issues=alt_issues,
            identified=meta_from_text(doc_id)[0] == doc_id or best.suffix.lower() in {".txt", ".md"},
            **classify(doc_id),
        )
        if (e.doc_id, e.issue) in VERIFIED:
            e.tier = "verified"
        elif health.get((e.doc_id, e.issue, e.source)) == "checked":
            e.tier = "checked"
        entries.append(e)
    entries.sort(key=lambda e: (e.family, e.doc_id))
    skipped = [p.relative_to(folder).as_posix() for p in folder.rglob("*")
               if p.is_file() and p.suffix.lower() not in SUPPORTED
               and not any(part.startswith(".") for part in p.relative_to(folder).parts)]
    return Catalogue(folder, entries, selection, skipped)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(prog="python -m spacestd.catalogue", description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", nargs="?", default="documents")
    ap.add_argument("--json", action="store_true", help="every entry as JSON")
    args = ap.parse_args()
    cat = build_catalogue(Path(args.folder))
    if args.json:
        print(json.dumps({"summary": cat.summary(), "entries": [e.to_dict(full=True) for e in cat.entries]},
                         indent=1, ensure_ascii=False))
        return
    s = cat.summary()
    print(f"{s['documents']} documents ({s['active']} active, {s['superseded']} superseded), {s['loaded']} loaded, "
          f"{s['skipped_files']} other files skipped")
    print("selection:", "top-level files only (no corpus.yaml)" if s["selection"] is None else s["selection"])
    print("\nby family and type:")
    for k, n in s["by_family_type"].items():
        print(f"  {n:4}  {k}")
    print("\nby discipline:")
    for k, n in s["by_discipline"].items():
        print(f"  {n:4}  {k}")
    print("\nloaded:")
    for e in cat.loaded():
        print(f"  {e.doc_id} {e.issue} [{e.tier}]  {e.source}")
    if s["issue_conflicts"]:
        print("\nsame doc_id, different issue (the first one is used):")
        for k, v in s["issue_conflicts"].items():
            print(f"  {k}: {' | '.join(i or '(none)' for i in v)}")
    if s["unidentified"]:
        print("\nno standard number found (add a .meta.yaml sidecar):")
        for k in s["unidentified"]:
            print(f"  {k}")


if __name__ == "__main__":
    main()
