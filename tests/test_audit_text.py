"""scripts/audit_standards_text.py (release plan C3) on the invented fixtures (ADR-0002)."""

import importlib.util
import shutil
import sys
from pathlib import Path

from spacestd.models import Cell, Document, Requirement, Table, TableRow

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("audit_standards_text", ROOT / "scripts" / "audit_standards_text.py")
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit  # dataclasses look the module up
spec.loader.exec_module(audit)

# 12 words, from tests/fixtures/demo_ecss.txt (invented text)
SENTENCE = "The supplier shall perform unit testing of all safety-critical software components."


def docs_folder(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    for name in ("demo_ecss.txt", "demo_ecss.meta.yaml"):
        shutil.copy(ROOT / "tests" / "fixtures" / name, docs / name)
    return docs


def write(tree: Path, rel: str, text: str | bytes) -> None:
    p = tree / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text if isinstance(text, bytes) else text.encode())


def run(tmp_path: Path, files: dict, capsys) -> tuple[int, str]:
    tree = tmp_path / "tree"
    tree.mkdir()
    for rel, text in files.items():
        write(tree, rel, text)
    code = audit.main(["--docs", str(docs_folder(tmp_path)), "--tree", str(tree), "--no-cache"])
    return code, capsys.readouterr().out


def test_words_are_normalised():
    assert audit.words("Safety‑critical “Unit” TESTING,\nof") == ["safety", "critical", "unit", "testing", "of"]


def test_copied_run_is_reported_with_line_and_length_only(tmp_path, capsys):
    # same words, other case and line breaks, inside a longer paragraph
    copied = "Intro line.\n\nAs written: " + SENTENCE.upper().replace(" unit ", "\nunit ") + " End.\n"
    code, out = run(tmp_path, {"notes/review.md": copied}, capsys)
    assert code == 1
    assert "- notes/review.md:3  12 words  (DEMO-E-ST-99C Rev.1)" in out
    assert "supplier" not in out.lower() and "safety" not in out.lower()


def test_eleven_words_and_paraphrases_pass(tmp_path, capsys):
    short = SENTENCE.removeprefix("The ")  # 11 words
    paraphrase = "Suppliers unit-test every safety-critical software component."
    code, out = run(tmp_path, {"a.md": short, "b.md": paraphrase}, capsys)
    assert code == 0
    assert "0 runs of >= 12 words, 0 table rows" in out


def test_overlapping_windows_merge_into_one_run(tmp_path, capsys):
    two = ("a. The supplier shall produce a software development plan covering the full life cycle.\n"
           "b. The software development plan shall identify the methods and tools used,\n"
           "including the configuration management tool.\n")
    code, out = run(tmp_path, {"x.md": two}, capsys)
    hits = [ln for ln in out.splitlines() if ln.startswith("- ")]
    assert code == 1  # the item letters are not in the parsed text, so the two runs stay apart
    assert hits == ["- x.md:1  13 words  (DEMO-E-ST-99C Rev.1)", "- x.md:2  16 words  (DEMO-E-ST-99C Rev.1)"]


def test_binary_and_documents_are_skipped(tmp_path, capsys):
    code, out = run(tmp_path, {"img.bin": b"\0\1" + SENTENCE.encode(), "documents/copy.txt": SENTENCE,
                               "documents/README.md": "Put your standards here."}, capsys)
    assert code == 0
    assert "1 text files checked (1 binary or non-UTF-8 skipped)" in out


def table_doc() -> Document:
    rows = [
        TableRow({"Part": "Widget bracket", "Case": "Ground test"},
                 {"Factor": Cell("1.25", 1.25), "Margin": Cell("0.15", 0.15)}),
        TableRow({"Part": "Pin"}, {"Factor": Cell("2")}),  # too short to judge
    ]
    table = Table("DEMO-E-ST-97C", "", "Table 9-9", "Invented factors", ["Part", "Case"], ["Factor", "Margin"], rows)
    req = Requirement("DEMO-E-ST-97C", "", "9.9.1a", "9.9.1", "The widget shall be invented.")
    return Document("DEMO-E-ST-97C", "", "Invented", "demo.txt", [req], [table])


def test_table_row_copied_whole():
    files = [
        audit.TreeFile.from_text("t.md", "| Part | Case | Factor | Margin |\n"
                                         "| Widget bracket | Ground test | 1.25 | 0.15 |\n"
                                         "| Widget bracket | Ground test | 1.25 | n/a |\n"
                                         "| Pin | 2 |\n"),
    ]
    a = audit.Audit(files)
    a.add_document(table_doc())
    hits = a.hits()
    assert [h.render() for h in hits] == ["t.md:2  4 fields, table row copied whole  (DEMO-E-ST-97C, Table 9-9)"]


def test_unparsed_document_fails_the_audit(tmp_path, capsys, monkeypatch):
    def broken(*args, **kwargs):
        raise ValueError("bad file")

    monkeypatch.setattr("spacestd.loaders.load_document", broken)
    code, out = run(tmp_path, {"a.md": "Nothing copied here."}, capsys)
    assert code == 1
    assert "against 0 parsed documents" in out
    assert "- DEMO-E-ST-99C Rev.1 (ValueError)" in out


def test_allowlisted_hit_is_accepted_not_failed(tmp_path, capsys):
    allow = tmp_path / "allow.yaml"
    allow.write_text("- file: notes/review.md\n  kind: words\n  length: 12\n  source: DEMO-E-ST-99C\n"
                     "  reason: invented\n")
    tree = tmp_path / "tree"
    write(tree, "notes/review.md", SENTENCE)
    write(tree, "other.md", SENTENCE)
    args = ["--docs", str(docs_folder(tmp_path)), "--tree", str(tree), "--no-cache", "--allowlist", str(allow)]
    code = audit.main(args)
    out = capsys.readouterr().out
    assert code == 1  # other.md is not allowlisted
    assert "- other.md:1  12 words" in out
    assert "- accepted: notes/review.md:1  12 words" in out
    (tree / "other.md").unlink()
    assert audit.main(args) == 0
    assert "1 more hits accepted" in capsys.readouterr().out


def test_allowlist_entry_does_not_match_other_length_or_source():
    hit = audit.Hit("a.md", 5, "words", 13, {"DEMO-E-ST-99C Rev.1"})
    ok = {"file": "a.md", "kind": "words", "length": 13, "source": "DEMO-E-ST"}
    assert audit.is_accepted(hit, [ok])
    assert not audit.is_accepted(hit, [{**ok, "length": 14}])
    assert not audit.is_accepted(hit, [{**ok, "source": "ECSS"}])
    assert not audit.is_accepted(hit, [{**ok, "file": "b.md"}])
    assert not audit.is_accepted(hit, [{**ok, "kind": "table row"}])
    assert not audit.is_accepted(audit.Hit("a.md", 5, "words", 13, {"DEMO-E-ST-99C", "ECSS-Q"}), [ok])
    both = audit.Hit("a.md", 5, "words", 13, {"DEMO-E-ST-99C", "ECSS-Q-ST-99C"})
    assert audit.is_accepted(both, [{**ok, "source": ["DEMO-E-ST", "ECSS-Q"]}])  # a list of prefixes


def test_repository_allowlist_is_well_formed():
    entries = audit.load_allowlist(ROOT / "scripts" / "audit_allowlist.yaml")
    assert len(entries) == 13
    assert all({"file", "kind", "length", "source", "reason"} <= set(e) for e in entries)
