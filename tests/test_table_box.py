"""H16 T4: a captioned box without inner rules is a one-column table (PDFs from tests/pdfgen.py)."""

from pdfgen import Page, write_pdf

from spacestd.pdf_extract import read_pdf

ENTRIES = ["10 Hz @ 0.01 g2/Hz", "10 to 50 Hz @ +3 dB/oct", "50 to 300 Hz @ 0.5 g2/Hz",
           "300 to 900 Hz @ -6 dB/oct", "900 to 2000 Hz @ 0.02 g2/Hz", "Overall = 3.3 units"]
X0, X1 = 200, 400


def _entries(page: Page, top: float = 120) -> None:
    for i, s in enumerate(ENTRIES[:-1]):
        page.text(240, top + 4 + i * 12, s)
    page.text(240, top + 4 + 5 * 12 + 14, ENTRIES[-1])


def _bars(page: Page, top: float = 115, bottom: float = 215) -> None:
    for a, b in [(X0, 270), (270, 340), (340, X1)]:  # rules made of touching segments
        page.bar(a, top, b, top + 1)
        page.bar(a, bottom, b, bottom + 1)
    page.bar(X0, top, X0 + 1, bottom + 1)
    page.bar(X1 - 1, top, X1, bottom + 1)


def _page(caption: bool = True, bars: bool = True) -> Page:
    page = Page()
    page.text(72, 60, "Body text before the table.")
    if caption:
        page.text(72, 95, "Table 2 - Invented Widget Levels", bold=True)
    if bars:
        _bars(page)
    else:
        page.box(X0, 115, X1, 215)
    _entries(page)
    page.text(72, 240, "Text after the table.")
    return page


def _read(tmp_path, page):
    return read_pdf(write_pdf(tmp_path / "t.pdf", [page]), "DOC-1", "A")


def test_boxed_table_found_with_rows(tmp_path):
    c = _read(tmp_path, _page())
    assert [t.table_id for t in c.tables] == ["Table 2"]
    t = c.tables[0]
    assert t.caption == "Invented Widget Levels" and t.page == 1
    assert t.value_columns == ["Entry"] and t.label_columns == []
    assert [r.cells["Entry"].text for r in t.rows] == ENTRIES
    assert all(r.labels == {} for r in t.rows)
    assert list(c.table_lines.values()) == ["Table 2"]


def test_box_lines_leave_the_text_flow(tmp_path):
    c = _read(tmp_path, _page())
    flow = " ".join(ln.text for ln in c.lines)
    assert "Hz" not in flow and "Overall" not in flow
    assert "Body text before" in flow and "Text after" in flow
    assert any(ln.text.startswith("Table 2") for ln in c.lines)


def test_box_drawn_with_lines(tmp_path):
    c = _read(tmp_path, _page(bars=False))
    assert [len(t.rows) for t in c.tables] == [6]


def test_box_without_caption_is_ignored(tmp_path):
    c = _read(tmp_path, _page(caption=False))
    assert c.tables == []
    assert "Overall" in " ".join(ln.text for ln in c.lines)


def test_caption_with_plain_text_gives_no_table(tmp_path):
    page = Page()
    page.text(72, 95, "Table 2 - Invented Widget Levels", bold=True)
    for i in range(4):
        page.text(72, 115 + i * 12, f"Plain sentence number {i} without any rules.")
    c = _read(tmp_path, page)
    assert c.tables == []


def test_ruled_table_on_same_page_still_works(tmp_path):
    page = _page()
    page.text(72, 300, "Table 3: Invented grid", bold=True)
    xs, ys = [72, 220, 330, 440], [320, 340, 360, 380]
    page.grid(xs, ys)
    for x, s in zip(xs, ["Widget", "Factor A", "Factor B"]):
        page.text(x + 4, ys[0] + 5, s, bold=True)
    for r, (n, a, b) in enumerate([("Sprocket", "1,25", "2,0"), ("Flange", "1,1", "1,5")], 1):
        for x, s in zip(xs, [n, a, b]):
            page.text(x + 4, ys[r] + 5, s)
    c = _read(tmp_path, page)
    by = {t.table_id: t for t in c.tables}
    assert set(by) == {"Table 2", "Table 3"}
    assert len(by["Table 2"].rows) == 6 and len(by["Table 3"].rows) == 2


def test_tight_spacing_real_like_layout(tmp_path):
    """Top rule 0.5 pt under the caption, first line 1 pt under the rule, thin rules with corner squares."""
    page = Page()
    page.text(72, 364, "Table 2 - Invented Widget Levels", size=12, bold=True)
    t, b = 376.7, 473.5
    for a, z in [(198.4, 260), (260, 330), (330, 413.7)]:
        page.bar(a, t, z, t + 0.48)
        page.bar(a, b, z, b + 0.48)
    page.bar(198.2, t, 198.68, t + 0.48)
    page.bar(413.5, t, 413.98, t + 0.48)
    page.bar(198.2, t + 0.48, 198.68, b)
    page.bar(413.5, t + 0.48, 413.98, b)
    for i, s in enumerate(ENTRIES[:5]):
        page.text(240, t + 1.5 + i * 14, s)
    page.text(240, t + 1.5 + 5 * 14 + 14, ENTRIES[5])
    c = _read(tmp_path, page)
    assert [r.cells["Entry"].text for r in c.tables[0].rows] == ENTRIES
    assert c.tables[0].caption == "Invented Widget Levels"
    assert "Hz" not in " ".join(ln.text for ln in c.lines)
