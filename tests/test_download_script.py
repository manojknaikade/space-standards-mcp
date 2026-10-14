"""scripts/download_nasa_standards.py against a fake site: invented listing HTML, no network."""

import importlib.util
import io
import json
import urllib.error
from pathlib import Path

import pytest

from spacestd.loaders import _manifest, manifest_record

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "download_nasa_standards.py"
spec = importlib.util.spec_from_file_location("download_nasa_standards", SCRIPT)
dl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dl)

BASE = dl.BASE_URL


def row(doc, ver, title, slug):
    return (
        "<tr>"
        f'<td class="views-field-field-std-document-number"><span data-link="no-link">{doc}</span></td>'
        f'<td class="views-field-field-std-document-version">{ver}</td>'
        f'<td class="views-field-title"><span data-link="no-link">{title}</span></td>'
        '<td class="views-field-field-document-date"><time datetime="x">2001-01-01</time></td>'
        f'<td><a href="/standard/{slug}">NTSS Summary Page</a></td>'
        "</tr>"
    )


def detail(pdf):
    return f'<div class="field--name-field-pub-upload-public-std"><a href="{pdf}">pdf</a></div>'


PDF = b"%PDF-1.4 invented"


def site(robots="User-agent: *\nDisallow: /private/\n"):
    pages = {
        f"{BASE}/robots.txt": robots.encode(),
        f"{BASE}/all-standards?page=0": (
            row("TEST-STD-0001", "A", "Invented one", "t1") + row("TEST-STD-0002", "Baseline", "Invented two", "t2")
        ).encode(),
        f"{BASE}/all-standards?page=1": row("TEST-STD-0003", "B", "Invented three", "t3").encode(),
        f"{BASE}/all-standards?page=2": row("TEST-STD-0003", "B", "Invented three", "t3").encode(),  # repeats
        f"{BASE}/standard/t1": detail("/sites/files/TEST-STD-0001A.pdf").encode(),
        f"{BASE}/standard/t2": detail("/sites/files/two%20final.pdf").encode(),
        f"{BASE}/standard/t3": detail("/private/TEST-STD-0003B.pdf").encode(),
        f"{BASE}/sites/files/TEST-STD-0001A.pdf": PDF,
        f"{BASE}/sites/files/two%20final.pdf": PDF + b" 2",
    }
    return pages


class FakeWeb:
    def __init__(self, pages):
        self.pages, self.requests = pages, []

    def __call__(self, req, timeout=None):
        url = req.full_url
        self.requests.append((url, req.get_header("User-agent")))
        if url not in self.pages:
            raise urllib.error.HTTPError(url, 404, "not found", {}, None)
        return io.BytesIO(self.pages[url])


class Clock:
    def __init__(self):
        self.t, self.sleeps = 0.0, []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(s)
        self.t += s


def fetcher(web, clock=None, delay=2.0):
    clock = clock or Clock()
    return dl.Fetcher(delay=delay, urlopen=web, sleep=clock.sleep, clock=clock)


def pdf_urls(web):
    return [u for u, _ in web.requests if u.endswith(".pdf")]


def test_full_run_honest_agent_robots_and_manifest(tmp_path):
    web = FakeWeb(site())
    recs = dl.run(fetcher(web), tmp_path, log=lambda *_: None)
    by = {r["doc_no"]: r for r in recs}
    assert [r["doc_no"] for r in recs] == ["TEST-STD-0001", "TEST-STD-0002", "TEST-STD-0003"]
    assert by["TEST-STD-0001"]["status"] == "downloaded"
    assert by["TEST-STD-0001"]["dest_filename"] == "TEST-STD-0001A.pdf"
    assert by["TEST-STD-0002"]["dest_filename"] == "TEST-STD-0002 - two final.pdf"
    assert by["TEST-STD-0003"]["status"] == "disallowed"  # robots.txt
    assert not by["TEST-STD-0003"]["download_success"]
    assert (tmp_path / "TEST-STD-0001A.pdf").read_bytes() == PDF
    # robots.txt first, the disallowed PDF never requested, honest User-Agent on every request
    assert web.requests[0][0] == f"{BASE}/robots.txt"
    assert f"{BASE}/private/TEST-STD-0003B.pdf" not in pdf_urls(web)
    assert {ua for _, ua in web.requests} == {dl.USER_AGENT}
    assert "Mozilla" not in dl.USER_AGENT and "space-standards-mcp" in dl.USER_AGENT

    data = json.loads((tmp_path / "manifest.json").read_text())
    assert data["schema_version"] == 2 and data["total_standards"] == 3
    assert data["total_bytes"] == len(PDF) + len(PDF) + 2
    assert all("local_path" not in r for r in data["standards"])
    assert len(by["TEST-STD-0001"]["sha256"]) == 64
    # the loader still reads it
    _manifest.cache_clear()
    assert manifest_record(tmp_path / "TEST-STD-0001A.pdf")["title"] == "Invented one"


def test_requests_are_spaced_by_the_delay(tmp_path):
    clock = Clock()
    dl.run(fetcher(FakeWeb(site()), clock, delay=3.0), tmp_path, log=lambda *_: None)
    assert clock.sleeps and all(s == pytest.approx(3.0) for s in clock.sleeps)


def test_crawl_delay_raises_the_interval():
    f = fetcher(FakeWeb(site("User-agent: *\nCrawl-delay: 7\n")))
    f.load_robots()
    assert f.delay == 7.0


def test_unreadable_robots_stops_the_run(tmp_path):
    def broken(req, timeout=None):
        raise urllib.error.URLError("down")

    with pytest.raises(RuntimeError, match="robots.txt"):
        dl.run(fetcher(broken), tmp_path, log=lambda *_: None)


def test_missing_robots_allows_and_forbidden_robots_blocks(tmp_path):
    pages = site()
    del pages[f"{BASE}/robots.txt"]  # 404: allowed
    web = FakeWeb(pages)
    recs = dl.run(fetcher(web), tmp_path / "a", log=lambda *_: None)
    assert [r["status"] for r in recs] == ["downloaded", "downloaded", "failed"]  # 3rd: no such PDF here

    def forbidden(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 403, "forbidden", {}, None)

    f = fetcher(forbidden)
    f.load_robots()
    assert not f.allowed(f"{BASE}/all-standards?page=0")


def test_second_run_downloads_nothing_again(tmp_path):
    dl.run(fetcher(FakeWeb(site())), tmp_path, log=lambda *_: None)
    web = FakeWeb(site())
    recs = dl.run(fetcher(web), tmp_path, log=lambda *_: None)
    assert pdf_urls(web) == []
    # not even the detail pages of the standards already present
    assert not {f"{BASE}/standard/t1", f"{BASE}/standard/t2"} & {u for u, _ in web.requests}
    assert [r["status"] for r in recs] == ["present", "present", "disallowed"]
    assert recs[0]["sha256"]  # carried over

    web = FakeWeb(site())
    dl.run(fetcher(web), tmp_path, force=True, log=lambda *_: None)
    assert len(pdf_urls(web)) == 2


def test_file_on_disk_without_manifest_is_not_fetched(tmp_path):
    (tmp_path / "TEST-STD-0001A.pdf").write_bytes(PDF)
    web = FakeWeb(site())
    recs = dl.run(fetcher(web), tmp_path, log=lambda *_: None)
    assert recs[0]["status"] == "present"
    assert pdf_urls(web) == [f"{BASE}/sites/files/two%20final.pdf"]


def test_only_and_dry_run(tmp_path):
    web = FakeWeb(site())
    recs = dl.run(fetcher(web), tmp_path, only=["test-std-0002"], dry_run=True, log=lambda *_: None)
    assert pdf_urls(web) == []
    assert not (tmp_path / "manifest.json").exists()
    assert [r.get("status") for r in recs] == [None, "listed", None]

    dl.run(fetcher(FakeWeb(site())), tmp_path, log=lambda *_: None)
    web = FakeWeb(site())
    recs = dl.run(fetcher(web), tmp_path, only=["TEST-STD-0002"], force=True, log=lambda *_: None)
    assert pdf_urls(web) == [f"{BASE}/sites/files/two%20final.pdf"]
    # records outside --only keep their earlier state
    assert [r["status"] for r in recs] == ["downloaded", "downloaded", "disallowed"]
    assert len(json.loads((tmp_path / "manifest.json").read_text())["standards"]) == 3


def test_not_a_pdf_fails_that_standard_only(tmp_path):
    pages = site()
    pages[f"{BASE}/sites/files/TEST-STD-0001A.pdf"] = b"<html>login</html>"
    recs = dl.run(fetcher(FakeWeb(pages)), tmp_path, log=lambda *_: None)
    assert recs[0]["status"] == "failed" and "not a PDF" in recs[0]["error"]
    assert recs[1]["status"] == "downloaded"
    assert not (tmp_path / "TEST-STD-0001A.pdf").exists()


def test_schema_1_manifest_is_taken_over(tmp_path):
    (tmp_path / "TEST-STD-0001A.pdf").write_bytes(PDF)
    (tmp_path / "manifest.json").write_text(json.dumps({"standards": [{
        "doc_no": "TEST-STD-0001", "version": "A", "detail_link": "/standard/t1",
        "dest_filename": "TEST-STD-0001A.pdf", "download_success": True, "local_path": "/abs/x.pdf",
    }]}))
    web = FakeWeb(site())
    recs = dl.run(fetcher(web), tmp_path, log=lambda *_: None)
    assert f"{BASE}/standard/t1" not in [u for u, _ in web.requests]
    assert recs[0]["status"] == "present" and "local_path" not in recs[0]


def test_contact_goes_into_the_user_agent(tmp_path, monkeypatch):
    seen = {}

    def fake_run(f, target, **kw):
        seen["ua"], seen["delay"] = f.user_agent, f.delay

    monkeypatch.setattr(dl, "run", fake_run)
    assert dl.main([str(tmp_path), "--contact", "someone@example.org", "--delay", "0"]) == 0
    assert seen["ua"].endswith("; someone@example.org)") and "space-standards-mcp" in seen["ua"]
    assert seen["delay"] == 1.0  # floor
