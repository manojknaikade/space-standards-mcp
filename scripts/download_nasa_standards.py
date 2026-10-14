#!/usr/bin/env python3
"""Download the public NASA technical standards listed on https://standards.nasa.gov/all-standards.

For local use only: the PDFs go into a gitignored folder (e.g. `documents/nasa/`) and are never committed.
ECSS standards are not covered (ecss.nl needs a registration; download those by hand).

Behaviour towards the site:
- an honest User-Agent naming this project (`--contact` adds an e-mail or URL to it);
- one request at a time, at least `--delay` seconds apart (default 2 s, or the robots.txt Crawl-delay
  when that is longer); retries back off;
- robots.txt is read first and every URL is checked against it; disallowed URLs are skipped, and the run
  stops if robots.txt cannot be read;
- no bulk re-download: a standard whose PDF is already in the target folder (from the manifest of an
  earlier run, or by file name) is not fetched again; `--force` re-downloads, `--only` limits the run to
  some document numbers, `--dry-run` lists what would be downloaded without fetching any PDF.

Usage: python scripts/download_nasa_standards.py [TARGET_DIR] [--only NASA-STD-5001 ...] [--dry-run]

Manifest format (`TARGET_DIR/manifest.json`, read by `spacestd.loaders.manifest_record` to supply titles
and IDs the file names lack)::

    {
      "schema_version": 2,
      "generated_at": "YYYY-MM-DD HH:MM:SS UTC",
      "source_url": "https://standards.nasa.gov/all-standards",
      "user_agent": "<User-Agent sent>",
      "total_standards": <int>,          # records in "standards"
      "total_bytes": <int>,              # size of all PDFs present in TARGET_DIR
      "standards": [                     # one record per listed standard, in listing order
        {
          "page": <int>,                 # listing page the standard was found on (0-based)
          "doc_no": "NASA-STD-…",        # document number as listed
          "version": "…",                # version / revision as listed ("" if none)
          "title": "…",                  # title as listed
          "date": "…",                   # document date as listed
          "detail_link": "/standard/…",  # NTSS summary page, relative to the site
          "pdf_url": "https://…",        # resolved public PDF ("" if not resolved)
          "orig_filename": "…",          # file name on the site
          "dest_filename": "…",          # file name in TARGET_DIR (the loader's key)
          "status": "downloaded" | "present" | "failed" | "disallowed" | "listed",
          "download_success": <bool>,    # true when the PDF is in TARGET_DIR (downloaded or present)
          "file_size": <int>,            # bytes, when the PDF is in TARGET_DIR
          "sha256": "…",                 # of the PDF, when downloaded or taken over from an earlier run
          "downloaded_at": "YYYY-MM-DD", # when the PDF was fetched
          "error": "…"                   # only when status is failed or disallowed
        }
      ]
    }

`status`: `downloaded` = fetched in this run; `present` = already in TARGET_DIR, not fetched again;
`failed` = could not be resolved or downloaded; `disallowed` = robots.txt forbids the URL; `listed` = only
listed (`--dry-run`). Records from an earlier manifest that this run did not touch (e.g. outside `--only`)
are kept as they were. A `README.md` with the same catalogue as a table is written next to the manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

BASE_URL = "https://standards.nasa.gov"
LIST_URL = f"{BASE_URL}/all-standards"
PROJECT_URL = "https://github.com/manojknaikade/space-standards-mcp"
USER_AGENT = f"space-standards-mcp-downloader/0.2 (+{PROJECT_URL})"
MANIFEST = "manifest.json"
MAX_PAGES = 20  # safety stop for the listing; the site has had two pages


class Fetcher:
    """Polite HTTP: honest User-Agent, robots.txt, one request at a time with a minimum interval."""

    def __init__(self, user_agent=USER_AGENT, delay=2.0, retries=3, timeout=60,
                 urlopen=urllib.request.urlopen, sleep=time.sleep, clock=time.monotonic):
        self.user_agent = user_agent
        self.delay = delay
        self.retries = retries
        self.timeout = timeout
        self._urlopen, self._sleep, self._clock = urlopen, sleep, clock
        self._last = None
        self.robots = None

    def _wait(self):
        if self._last is not None:
            left = self.delay - (self._clock() - self._last)
            if left > 0:
                self._sleep(left)
        self._last = self._clock()

    def _get(self, url):
        self._wait()
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with self._urlopen(req, timeout=self.timeout) as resp:
            return resp.read()

    def load_robots(self, base=BASE_URL):
        """Read robots.txt (a missing one allows all); raises if it cannot be read at all."""
        rp = urllib.robotparser.RobotFileParser(f"{base}/robots.txt")
        try:
            lines = self._get(rp.url).decode("utf-8", errors="replace").splitlines()
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                rp.disallow_all = True
            elif 400 <= e.code < 500:
                rp.allow_all = True
            else:
                raise RuntimeError(f"cannot read {rp.url}: {e}") from e
        except OSError as e:
            raise RuntimeError(f"cannot read {rp.url}: {e}") from e
        else:
            rp.parse(lines)
        crawl = rp.crawl_delay(self.user_agent)
        if crawl and float(crawl) > self.delay:
            self.delay = float(crawl)
        self.robots = rp

    def allowed(self, url):
        return self.robots is None or self.robots.can_fetch(self.user_agent, url)

    def fetch(self, url):
        if not self.allowed(url):
            raise PermissionError(f"robots.txt disallows {url}")
        for attempt in range(self.retries):
            try:
                return self._get(url)
            except urllib.error.HTTPError as e:
                if e.code < 500 and e.code != 429 or attempt == self.retries - 1:
                    raise RuntimeError(f"failed to fetch {url}: {e}") from e
            except OSError as e:
                if attempt == self.retries - 1:
                    raise RuntimeError(f"failed to fetch {url}: {e}") from e
            self._sleep(self.delay * 2 ** (attempt + 1))
        raise AssertionError("unreachable")


def parse_listing(html, page_num):
    items = []
    for r in re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL):
        m_link = re.search(r'<a href="(/standard/[^"]+)"[^>]*>NTSS Summary Page</a>', r)
        if not m_link:
            continue
        m_doc = re.search(r'views-field-field-std-document-number[^>]*>.*?data-link="no-link">([^<]+)<', r, re.DOTALL)
        m_ver = re.search(r'views-field-field-std-document-version[^>]*>([^<]+)<', r, re.DOTALL)
        m_title = re.search(r'views-field-title[^>]*>.*?data-link="no-link">([^<]+)<', r, re.DOTALL)
        m_date = re.search(r'views-field-field-document-date.*?<time[^>]*>([^<]+)<', r, re.DOTALL)
        items.append({
            "page": page_num,
            "doc_no": m_doc.group(1).strip() if m_doc else "",
            "version": m_ver.group(1).strip() if m_ver else "",
            "title": m_title.group(1).strip() if m_title else "",
            "date": m_date.group(1).strip() if m_date else "",
            "detail_link": m_link.group(1),
        })
    return items


def list_standards(fetcher):
    """All listing pages, until a page adds no new standard."""
    items, seen = [], set()
    for page in range(MAX_PAGES):
        html = fetcher.fetch(f"{LIST_URL}?page={page}").decode("utf-8", errors="replace")
        new = [i for i in parse_listing(html, page) if i["detail_link"] not in seen]
        if not new:
            break
        seen.update(i["detail_link"] for i in new)
        items += new
    return items


def pdf_link(html):
    m = re.search(r'field--name-field-pub-upload-public-std.*?href="([^"]+\.pdf)"', html, re.DOTALL)
    if m:
        return m.group(1)
    any_pdf = re.search(r'href="([^"]+\.pdf)"', html)
    return any_pdf.group(1) if any_pdf else None


def dest_name(doc_no, orig_filename):
    clean_doc = re.sub(r"[^a-zA-Z0-9]", "", doc_no).lower()
    clean_file = re.sub(r"[^a-zA-Z0-9]", "", orig_filename).lower()
    name = orig_filename if clean_file.startswith(clean_doc) else f"{doc_no} - {orig_filename}"
    return name.replace("/", "_").replace("\\", "_").lstrip(".")


def resolve(fetcher, item):
    url = urllib.parse.urljoin(BASE_URL, item["detail_link"])
    rel = pdf_link(fetcher.fetch(url).decode("utf-8", errors="replace"))
    if not rel:
        raise RuntimeError(f"no PDF found on {url}")
    orig = urllib.parse.unquote(rel.split("/")[-1])
    item["orig_filename"] = orig
    item["dest_filename"] = dest_name(item["doc_no"], orig)
    item["pdf_url"] = urllib.parse.urljoin(BASE_URL, urllib.parse.quote(urllib.parse.unquote(rel), safe="/:?=&"))
    return item


def is_pdf(path):
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"%PDF"
    except OSError:
        return False


def download(fetcher, item, target):
    data = fetcher.fetch(item["pdf_url"])
    if not data.startswith(b"%PDF"):
        raise ValueError(f"not a PDF (starts with {data[:16]!r})")
    dest = target / item["dest_filename"]
    tmp = dest.with_name(dest.name + ".part")
    tmp.write_bytes(data)
    os.replace(tmp, dest)
    item.update(file_size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                downloaded_at=time.strftime("%Y-%m-%d", time.gmtime()))


def load_manifest(target):
    try:
        data = json.loads((target / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    recs = data.get("standards", []) if isinstance(data, dict) else []
    recs = [r for r in recs if isinstance(r, dict) and r.get("detail_link")]
    for r in recs:
        r.pop("local_path", None)  # schema 1 stored an absolute path; the file name is enough
    return recs


def _matches(item, only):
    norm = re.sub(r"[^a-z0-9]", "", item["doc_no"].lower())
    return any(norm.startswith(re.sub(r"[^a-z0-9]", "", o.lower())) for o in only)


def _set_status(item, status, error=None):
    item["status"] = status
    item["download_success"] = status in ("downloaded", "present")
    item.pop("error", None)
    if error:
        item["error"] = error


def run(fetcher, target, only=(), force=False, dry_run=False, log=print):
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    fetcher.load_robots()
    previous = {r["detail_link"]: r for r in load_manifest(target)}

    log(f"Listing {LIST_URL} …")
    listed = list_standards(fetcher)
    todo = [i for i in listed if not only or _matches(i, only)]
    log(f"  {len(listed)} standards listed, {len(todo)} selected")

    for n, item in enumerate(todo, 1):
        old = previous.get(item["detail_link"], {})
        same = old.get("version") == item["version"] and old.get("dest_filename")
        if same and not force and is_pdf(target / old["dest_filename"]):
            # known from the last run and on disk: no request at all
            for k in ("orig_filename", "dest_filename", "pdf_url", "sha256", "downloaded_at"):
                if k in old:
                    item[k] = old[k]
            item["file_size"] = (target / item["dest_filename"]).stat().st_size
            _set_status(item, "present")
        else:
            try:
                resolve(fetcher, item)
                dest = target / item["dest_filename"]
                if is_pdf(dest) and not force:
                    item["file_size"] = dest.stat().st_size
                    _set_status(item, "present")
                elif dry_run:
                    _set_status(item, "listed")
                else:
                    download(fetcher, item, target)
                    _set_status(item, "downloaded")
            except PermissionError as e:
                _set_status(item, "disallowed", str(e))
            except Exception as e:  # one failed standard must not stop the run
                _set_status(item, "failed", str(e))
        log(f"  [{n}/{len(todo)}] {item['status']:<10} {item['doc_no']} -> {item.get('dest_filename', '')}")

    # keep earlier records this run did not touch (outside --only, or no longer listed)
    done = {i["detail_link"] for i in todo}
    records = [i if i["detail_link"] in done else previous.get(i["detail_link"], i) for i in listed]
    listed_links = {i["detail_link"] for i in listed}
    records += [r for link, r in previous.items() if link not in listed_links]
    if not dry_run:
        write_manifest(target, records, fetcher.user_agent)
    counts = {}
    for i in todo:
        counts[i["status"]] = counts.get(i["status"], 0) + 1
    log("  " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    return records


def write_manifest(target, records, user_agent):
    total_bytes = sum(r.get("file_size", 0) for r in records if r.get("download_success"))
    (target / MANIFEST).write_text(json.dumps({
        "schema_version": 2,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "source_url": LIST_URL,
        "user_agent": user_agent,
        "total_standards": len(records),
        "total_bytes": total_bytes,
        "standards": records,
    }, indent=2), encoding="utf-8")
    lines = [
        "# NASA Technical Standards\n",
        f"Source: [NASA Technical Standards System]({LIST_URL})\n",
        f"- **Total Standards:** {len(records)}",
        f"- **Total Size:** {total_bytes / 2**20:.2f} MB",
        f"- **Updated:** {time.strftime('%Y-%m-%d', time.gmtime())}\n",
        "## Standards Catalog\n",
        "| # | Document Number | Version | Title | Date | Status | File Size | File Name |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for n, r in enumerate(records, 1):
        lines.append(f"| {n} | {r.get('doc_no', '')} | {r.get('version', '')} | {r.get('title', '')} | {r.get('date', '')} | "
                     f"{r.get('status', '')} | {r.get('file_size', 0) / 2**20:.2f} MB | `{r.get('dest_filename', '')}` |")
    (target / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("target", nargs="?", default="documents/nasa", help="download folder (default: documents/nasa)")
    ap.add_argument("--only", nargs="+", default=(), metavar="DOC_NO",
                    help="only these document numbers (prefix match, e.g. NASA-STD-5001)")
    ap.add_argument("--force", action="store_true", help="re-download PDFs already in the target folder")
    ap.add_argument("--dry-run", action="store_true", help="list and resolve, download nothing, write no manifest")
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between requests (minimum 1; default 2)")
    ap.add_argument("--contact", default="", help="e-mail or URL added to the User-Agent")
    args = ap.parse_args(argv)
    ua = f"{USER_AGENT[:-1]}; {args.contact})" if args.contact else USER_AGENT
    fetcher = Fetcher(user_agent=ua, delay=max(args.delay, 1.0))
    try:
        run(fetcher, args.target, only=args.only, force=args.force, dry_run=args.dry_run)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
