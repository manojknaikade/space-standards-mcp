"""scripts/check_release_tree.py (release plan C6): path lists only, no git needed."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("check_release_tree", ROOT / "scripts" / "check_release_tree.py")
guard = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = guard
spec.loader.exec_module(guard)


def test_clean_tree_passes():
    assert guard.forbidden(["README.md", "src/spacestd/a.py", "documents/README.md", "tests/fixtures/demo.txt"]) == []


def test_forbidden_suffixes_anywhere():
    paths = ["a.pdf", "x/B.PDF", "c.doc", "d/e.docx", "f.pkl", "g.pdf.txt", "docx"]
    assert guard.forbidden(paths) == ["a.pdf", "c.doc", "d/e.docx", "f.pkl", "x/B.PDF"]


def test_documents_folder_only_keeps_its_readme():
    paths = ["documents/README.md", "documents/corpus.yaml", "documents/sub/x.txt", "other/documents/y.txt"]
    assert guard.forbidden(paths) == ["documents/corpus.yaml", "documents/sub/x.txt"]


def test_main_fails_and_names_paths(monkeypatch, capsys):
    monkeypatch.setattr(guard, "tracked_files", lambda root=ROOT: ["ok.md", "documents/x.txt", "s.pdf"])
    monkeypatch.setattr(guard, "load_excludes", lambda path=None: ["ok.md"])
    assert guard.main() == 1
    err = capsys.readouterr().err
    assert "documents/x.txt" in err and "s.pdf" in err and "ok.md" not in err


def test_main_passes_on_clean_list(monkeypatch):
    monkeypatch.setattr(guard, "tracked_files", lambda root=ROOT: ["ok.md", "documents/README.md"])
    monkeypatch.setattr(guard, "load_excludes", lambda path=None: ["ok.md"])
    assert guard.main() == 0


def test_load_excludes_skips_comments_and_blanks(tmp_path):
    f = tmp_path / "ex.txt"
    f.write_text("# header\n\ndocs/A.md\n  notes/*.md  \n# x\n", encoding="utf-8")
    assert guard.load_excludes(f) == ["docs/A.md", "notes/*.md"]


def test_excluded_glob_and_sorted():
    paths = ["notes/b.md", "docs/A.md", "notes/a.md", "other.md"]
    assert guard.excluded(paths, ["docs/A.md", "notes/*.md"]) == ["docs/A.md", "notes/a.md", "notes/b.md"]
    assert guard.excluded(paths, []) == []


def test_stale_pattern_detected():
    assert guard.stale_patterns(["docs/A.md"], ["docs/A.md", "gone/*.md"]) == ["gone/*.md"]


def test_link_detection():
    pats = ["docs/PROGRESS.md"]
    assert guard.excluded_links("docs/adr/x.md", "see [log](../PROGRESS.md)", pats) == [(1, "../PROGRESS.md")]
    assert guard.excluded_links("docs/x.md", "a\n[f](PROGRESS.md#round-4)", pats) == [(2, "PROGRESS.md#round-4")]
    assert guard.excluded_links("README.md", "[f](docs/PROGRESS.md)", pats) == [(1, "docs/PROGRESS.md")]
    assert guard.excluded_links("docs/x.md", "[o](OTHER.md)", pats) == []
    assert guard.excluded_links("docs/x.md", "[u](https://example.org/docs/PROGRESS.md)", pats) == []
    assert guard.excluded_links("docs/x.md", "[a](#PROGRESS.md)", pats) == []


def test_main_default_fails_on_stale_pattern(monkeypatch, capsys):
    monkeypatch.setattr(guard, "tracked_files", lambda root=ROOT: ["ok.md", "docs/A.md"])
    monkeypatch.setattr(guard, "load_excludes", lambda path=None: ["docs/A.md", "gone.md"])
    assert guard.main() == 1
    assert "gone.md" in capsys.readouterr().err


def test_main_default_runs_release_checks_when_every_entry_is_gone(monkeypatch, tmp_path, capsys):
    # the public release tree: no excluded file tracked, so the guard checks it as the release tree
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    (tmp_path / "ok.md").write_text("see [log](docs/A.md)", encoding="utf-8")
    monkeypatch.setattr(guard, "tracked_files", lambda root=ROOT: ["ok.md"])
    monkeypatch.setattr(guard, "load_excludes", lambda path=None: ["docs/A.md"])
    assert guard.main() == 1  # the release checks run: a link into an excluded file fails
    assert "ok.md:1" in capsys.readouterr().err
    (tmp_path / "ok.md").write_text("no links", encoding="utf-8")
    assert guard.main() == 0
    assert "no excluded files or links to them" in capsys.readouterr().out


def test_main_release_fails_on_tracked_excluded_file(monkeypatch, capsys):
    monkeypatch.setattr(guard, "tracked_files", lambda root=ROOT: ["ok.md", "docs/A.md"])
    monkeypatch.setattr(guard, "load_excludes", lambda path=None: ["docs/A.md"])
    assert guard.main(["--release"]) == 1
    assert "docs/A.md" in capsys.readouterr().err
