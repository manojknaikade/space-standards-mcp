#!/usr/bin/env python3
"""Download public NASA Procedural Requirements (NPRs) from the NODIS library, https://nodis3.gsfc.nasa.gov.

For local use only: the PDFs go into a gitignored folder (e.g. `documents/npr/`) and are never committed.
The current revision of each NPR is read from the NODIS library listing, so the copy is the one in force on
the day of the download; `manifest.json` in the target folder records revision, title, URL and download date.

Behaviour towards the site: a User-Agent naming this project (`--contact` adds an e-mail or URL), one request
at a time at least `--delay` seconds apart, nothing fetched twice (a PDF already in the folder is kept unless
`--force`). Standard library only.

    python scripts/download_nasa_nprs.py documents/npr                 # the default set below
    python scripts/download_nasa_nprs.py documents/npr --only 7150.2 7123.1
    python scripts/download_nasa_nprs.py documents/npr --dry-run
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://nodis3.gsfc.nasa.gov"
# NPRs that space projects are asked about: project management, systems and software engineering, risk,
# safety and mission assurance, orbital debris, planetary protection, quality
DEFAULT = ["7120.5", "7120.8", "7120.10", "7123.1", "7150.2", "8000.4", "8079.1", "8621.1", "8705.2", "8705.4",
           "8705.6", "8715.3", "8715.5", "8715.6", "8715.7", "8715.24", "8715.26", "8735.1", "8735.2"]
ROW_RE = re.compile(r'displayDir\.cfm\?t=NPR&c=(\d{4})&s=(\d+)([A-Z]?)"[^>]*>.*?</a>(.*?)</tr>', re.S)


def fetch(url: str, agent: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": agent})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def listing(page: str) -> list[dict]:
    """NPRs on one library listing page: number, revision letter and title (the listing's own text)."""
    out = []
    for chapter, sub, rev, rest in ROW_RE.findall(page):
        title = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", rest)).split())
        # the listing prints the title, then the expiration date
        name = re.sub(r"\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)"
                      r"\s+\d{1,2},\s+\d{4}\s*$", "", title)
        out.append({"number": f"{chapter}.{sub}", "revision": rev, "title": name, "listing_text": title})
    return out


def pdf_url(number: str, revision: str) -> str:
    """NODIS file naming: NPR 7150.2D -> npg_img/N_PR_7150_002D_/N_PR_7150_002D_.pdf; a baseline issue has
    four digits and no letter (NPR 8715.24 -> N_PR_8715_0024_)."""
    chapter, sub = number.split(".")
    stem = f"N_PR_{chapter}_{int(sub):03d}{revision}_" if revision else f"N_PR_{chapter}_{int(sub):04d}_"
    return f"{BASE}/npg_img/{stem}/{stem}.pdf"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("target", nargs="?", default="documents/npr")
    ap.add_argument("--only", nargs="*", help="NPR numbers without the revision letter, e.g. 7150.2")
    ap.add_argument("--delay", type=float, default=2.0)
    ap.add_argument("--contact", default="", help="e-mail or URL added to the User-Agent")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    agent = "space-standards-mcp (personal, local use)" + (f"; {args.contact}" if args.contact else "")
    wanted = args.only or DEFAULT
    target = Path(args.target)

    found: dict[str, dict] = {}
    for series in sorted({n[0] for n in wanted}):
        page = fetch(f"{BASE}/lib_docs.cfm?range={series}", agent).decode("utf-8", "replace")
        found.update({r["number"]: r for r in listing(page)})
        time.sleep(args.delay)

    records, failed = [], 0
    for number in wanted:
        rec = found.get(number)
        if rec is None:
            print(f"NPR {number}: not in the NODIS listing", file=sys.stderr)
            failed += 1
            continue
        name = f"NPR {number}{rec['revision']}.pdf"
        rec = {**rec, "doc_no": f"NPR {number}{rec['revision']}", "pdf_url": pdf_url(number, rec["revision"]),
               "dest_filename": name}
        dest = target / name
        if args.dry_run:
            rec["status"] = "listed"
        elif dest.exists() and not args.force:
            rec["status"] = "present"
        else:
            try:
                data = fetch(rec["pdf_url"], agent, timeout=180)
                if not data.startswith(b"%PDF"):
                    raise ValueError("not a PDF")
                target.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                rec.update(status="downloaded", file_size=len(data),
                           downloaded=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            except Exception as e:  # keep going: one missing file must not stop the rest
                rec["status"] = f"failed: {type(e).__name__}"
                failed += 1
            time.sleep(args.delay)
        print(f"{rec['doc_no']}: {rec['status']}")
        records.append(rec)
    if not args.dry_run and records:
        target.mkdir(parents=True, exist_ok=True)  # also when every download failed
        manifest = target / "manifest.json"
        old = {}
        if manifest.exists():
            old = {r["doc_no"]: r for r in json.loads(manifest.read_text(encoding="utf-8")).get("standards", [])}
        for r in records:  # a file kept from an earlier run keeps its download date
            if r["status"] == "present" and r["doc_no"] in old:
                r.update({k: old[r["doc_no"]][k] for k in ("downloaded", "file_size") if k in old[r["doc_no"]]})
        merged = {**old, **{r["doc_no"]: r for r in records}}
        manifest.write_text(json.dumps({
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"), "source_url": BASE,
            "standards": list(merged.values())}, indent=1) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
