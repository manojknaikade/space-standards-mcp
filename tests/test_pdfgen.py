"""The test PDF writer (tests/pdfgen.py) gives pdfplumber real geometry: text positions, rules, rotation."""

import pdfplumber
from pdfgen import Page, write_pdf

from spacestd.pdf_extract import read_pdf


def _demo_table(page: Page) -> None:
    page.text(72, 80, "Table 9-9: Invented widget factors", size=11, bold=True)
    xs, ys = [72, 220, 330, 440], [100, 120, 140, 160]
    page.grid(xs, ys)
    for x, s in zip(xs, ["Widget", "Factor A", "Factor B"]):
        page.text(x + 4, ys[0] + 5, s, bold=True)
    for r, (name, a, b) in enumerate([("Sprocket", "1,25", "2,0"), ("Flange", "1,1", "1,5")], 1):
        for x, s in zip(xs, [name, a, b]):
            page.text(x + 4, ys[r] + 5, s)


def test_text_and_rules_land_where_asked(tmp_path):
    page = Page()
    page.text(100, 200, "Hello", size=10)
    page.hline(300, 72, 540)
    with pdfplumber.open(str(write_pdf(tmp_path / "a.pdf", [page]))) as pdf:
        p = pdf.pages[0]
        w = p.extract_words()[0]
        assert w["text"] == "Hello" and abs(w["x0"] - 100) < 0.5 and abs(w["top"] - 200) < 1.5
        assert len(p.lines) == 1 and abs(p.lines[0]["top"] - 300) < 0.5


def test_bold_and_rotated_text(tmp_path):
    page = Page()
    page.text(100, 100, "Bold", bold=True)
    page.text(300, 400, "Up", rotate=90)
    with pdfplumber.open(str(write_pdf(tmp_path / "b.pdf", [page]))) as pdf:
        chars = pdf.pages[0].chars
        assert all("Bold" in c["fontname"] for c in chars if c["text"] in "Bold")
        up = [c for c in chars if c["text"] in "Up"]
        assert [round(c["matrix"][1]) for c in up] == [1, 1]  # turned 90°, reads bottom to top
        assert up[0]["bottom"] > up[1]["bottom"]  # 'U' below 'p'


def test_read_pdf_finds_the_ruled_table(tmp_path):
    page = Page()
    _demo_table(page)
    content = read_pdf(write_pdf(tmp_path / "t.pdf", [page]), doc_id="X-1")
    (t,) = content.tables
    assert t.table_id == "Table 9-9" and t.caption == "Invented widget factors"
    assert t.label_columns == ["Widget"] and t.value_columns == ["Factor A", "Factor B"]
    assert [(r.labels["Widget"], r.cells["Factor A"].value) for r in t.rows] == [("Sprocket", 1.25), ("Flange", 1.1)]
