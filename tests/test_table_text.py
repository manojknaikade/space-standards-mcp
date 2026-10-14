"""Table cell text: rotated headers, Symbol-font glyphs, superscript markers (invented content only)."""

from pathlib import Path

import pdfplumber
from pdfgen import Page, write_pdf

from spacestd.pdf_extract import LSUP, _cell_lines, _split_size_runs, clean_label, normalise, parse_cell, read_pdf


def _lines(tmp_path: Path, page: Page, bbox):
    path = write_pdf(tmp_path / "t.pdf", [page])
    with pdfplumber.open(str(path)) as pdf:
        return [t for t, _, _ in _cell_lines(pdf.pages[0], bbox)]


def test_rotated_header_up_and_down(tmp_path):
    p = Page()
    p.text(110, 160, "Widgets bar", rotate=90)
    assert _lines(tmp_path, p, (100, 100, 130, 170)) == ["Widgets bar"]
    p = Page()
    p.text(110, 110, "Widgets bar", rotate=-90)
    assert _lines(tmp_path, p, (100, 100, 130, 180)) == ["Widgets bar"]


def test_two_rotated_lines_in_one_cell(tmp_path):
    p = Page()
    p.text(105, 160, "Alpha", rotate=90)
    p.text(120, 160, "Beta gamma", rotate=90)
    assert _lines(tmp_path, p, (100, 100, 140, 170)) == ["Alpha", "Beta gamma"]
    p = Page()
    p.text(115, 110, "Alpha", rotate=-90)  # reads top to bottom: the right line comes first
    p.text(130, 110, "Beta gamma", rotate=-90)
    assert _lines(tmp_path, p, (100, 100, 150, 180)) == ["Beta gamma", "Alpha"]


def test_rotated_header_row_over_normal_body(tmp_path):
    p = Page()
    p.text(72, 80, "Table 9-9: Invented widget factors", size=11, bold=True)
    p.grid([72, 172, 232, 292], [100, 170, 190])
    p.text(76, 110, "Item")
    p.text(190, 165, "Widgets", rotate=90)
    p.text(250, 165, "Gadgets", rotate=90)
    p.text(76, 175, "Bolt")
    p.text(176, 175, "1.5")
    p.text(236, 175, "2.5")
    content = read_pdf(write_pdf(tmp_path / "t.pdf", [p]))
    assert content.tables
    blob = repr(content.tables[0])
    assert "Widgets" in blob and "Gadgets" in blob and "s t e" not in blob


def test_symbol_glyphs_in_normalise():
    assert normalise("0.4  w  1.6") == "0.4 ≤ w ≤ 1.6"
    assert normalise("w  3.1  ") == "w ≥ 3.1 ± °"
    assert normalise("") == "×÷∞≠≈→√∂"
    greek = ""
    assert normalise(greek) == "αβγδΔελμπρσΣτθωΩ"
    assert normalise("ab") == "ab"  # unmapped stays


def _ch(text, x0, size=10.0, top=0.0):
    return {"text": text, "x0": x0, "x1": x0 + 0.6 * size, "top": top, "bottom": top + size, "size": size,
            "fontname": "Body-Roman", "upright": True}


def _cell_text(main, sup):
    chars = [_ch(c, 10 + 5 * i) for i, c in enumerate(main)]
    chars += [_ch(c, 10 + 5 * len(main) + 3 * i, 6.5, -2) for i, c in enumerate(sup)]
    return normalise(_split_size_runs(main + sup, chars))


def test_digits_after_letter_get_marker():
    assert _cell_text("Bays", "1") == "Bays" + LSUP + "1"
    assert _cell_text("g", "12") == "g" + LSUP + "12"
    assert LSUP not in _cell_text("g", "a")
    chars = [_ch(c, 10 + 5 * i) for i, c in enumerate("m2")]  # same size: plain text
    assert _split_size_runs("m2", chars) == "m2"


def test_parse_cell_footnote_key_vs_exponent():
    cell = parse_cell(_cell_text("Bays", "1") + " 1 and 3", {"1", "2"})
    assert cell.text == "Bays 1 and 3" and cell.footnotes == ["1"]
    cell = parse_cell(_cell_text("g", "2") + "/Hz", {"1"})
    assert cell.text == "g²/Hz" and cell.footnotes == []
    assert clean_label(_cell_text("Bays", "1"), {"1"}) == "Bays"
    assert clean_label(_cell_text("m", "2"), {"1"}) == "m²"


def test_rotated_small_text_keeps_word_spaces(tmp_path):
    for rot, top in ((90, 170), (-90, 100)):
        p = Page()
        p.text(110, top, "Aluminium Copper alloys", size=8, rotate=rot)
        assert _lines(tmp_path, p, (100, 50, 130, 260)) == ["Aluminium Copper alloys"]
