"""H19: shaded cells ("required"), their swatch legend and marker footnotes; degenerate tables are dropped."""

from pdfgen import Page, write_pdf

from spacestd.index import _row_text
from spacestd.models import Cell, Table, TableRow
from spacestd.pdf_extract import is_degenerate, read_pdf

XS = [72, 200, 280, 360, 440]
YS = [100, 120, 140, 160, 180, 200]


def _table_page(with_legend: bool = True, shade: bool = True) -> Page:
    page = Page()
    page.text(72, 70, "Table 1 - Invented Test Matrix", bold=True)
    page.grid(XS, YS)
    for x, h in zip(XS[1:], ["Component", "Subsystem", "Payload"]):
        page.text(x + 4, 104, h, bold=True)
    for i, label in enumerate(["Alpha test", "Beta test", "Gamma test", "Delta test"]):
        page.text(76, YS[i + 1] + 4, label)
    if shade:
        page.fill(200.5, 120.5, 279.5, 139.5, 0.8)       # row 1 Component: shaded, no text
        page.fill(280.5, 120.5, 359.5, 130, 0.8)          # row 1 Subsystem: two rects
        page.fill(280.5, 130, 359.5, 139.5, 0.8)
        page.text(284, 124, "2 >")
        page.fill(360.5, 120.5, 439.5, 139.5, 0.749)      # row 1 Payload: the darker grey
        page.text(364, 124, "1")
        page.text(204, 144, ">")                           # row 2: unshaded cell with text
        page.fill(280.5, 140.5, 359.5, 159.5, 0.8)
        page.text(284, 144, "2,3")
        page.fill(360.5, 160.5, 439.5, 179.5, 0.0)         # black fill: not shading
        page.text(204, 164, "2 <454 kg")                   # row 3 Component unshaded, marker plus limit
        page.fill(200.5, 180.5, 279.5, 199.5, 1.0)         # white fill: not shading
        page.text(284, 184, "1,25")
    if with_legend:
        page.fill(91.5, 217.4, 127.8, 227.7, 0.8)
        page.text(130.7, 218.9, "Invented must-do mark.")
        page.text(91.2, 232, ">", bold=True)
        page.text(100, 232, "Tested with a margin.")
        page.text(91.2, 244, "1", bold=True)
        page.text(100, 244, "First invented note")
        page.text(108, 255, "that wraps here.")
        page.text(91.2, 267, "2", bold=True)
        page.text(100, 267, "Second note.")
        page.text(72, 300, "A later body paragraph.")
    return page


def _read(tmp_path, page):
    return read_pdf(write_pdf(tmp_path / "t.pdf", [page]), "INV-1", "A").tables[0]


def test_shaded_cells_and_legend(tmp_path):
    t = _read(tmp_path, _table_page())
    r = [row.cells for row in t.rows]
    names = t.value_columns
    assert [r[0][n].shaded for n in names] == [True, True, True]
    assert [r[1][n].shaded for n in names] == [False, True, False]
    assert not r[2][names[0]].shaded and not r[2][names[2]].shaded  # black fill is a rule, not shading
    assert not r[3][names[0]].shaded  # white fill
    assert t.footnotes["shaded"] == "Invented must-do mark."
    assert t.footnotes[">"] == "Tested with a margin."
    assert t.footnotes["1"] == "First invented note that wraps here."
    assert t.footnotes["2"] == "Second note."


def test_marker_footnotes_in_cells(tmp_path):
    t = _read(tmp_path, _table_page())
    r = [row.cells for row in t.rows]
    n = t.value_columns
    assert r[0][n[1]].text == "2 >" and r[0][n[1]].footnotes == ["2", ">"] and r[0][n[1]].value is None
    assert r[0][n[2]].footnotes == ["1"] and r[0][n[2]].value is None
    assert r[0][n[0]].text == "" and r[0][n[0]].footnotes == []
    assert r[1][n[0]].footnotes == [">"]
    assert r[1][n[1]].footnotes == ["2"]  # '3' has no legend entry
    assert r[2][n[0]].text == "2 <454 kg" and r[2][n[0]].footnotes == ["2"]
    assert r[3][n[1]].text == "1,25" and r[3][n[1]].footnotes == [] and r[3][n[1]].value == 1.25


def test_legend_lines_leave_the_text_flow(tmp_path):
    content = read_pdf(write_pdf(tmp_path / "t.pdf", [_table_page()]), "INV-1", "A")
    texts = [ln.text for ln in content.lines]
    assert "A later body paragraph." in texts
    assert not any("Required" in x or "Second note" in x or "wraps" in x for x in texts)


def test_row_text_shows_shading(tmp_path):
    t = _read(tmp_path, _table_page())
    assert "Invented must-do mark." in _row_text(t, t.rows[0])
    assert "Invented must-do mark." not in _row_text(t, t.rows[3])
    assert t.rows[0].cells[t.value_columns[0]].to_dict()["shaded"] is True
    assert "shaded" not in t.rows[3].cells[t.value_columns[0]].to_dict()


def test_shaded_without_legend_text_says_shaded():
    t = Table("D", "A", "Table 1", "c", [], ["V"], [TableRow({}, {"V": Cell("x", shaded=True)})])
    assert _row_text(t, t.rows[0]).endswith("x shaded")


def test_table_without_shading_is_unchanged(tmp_path):
    t = _read(tmp_path, _table_page(with_legend=False, shade=False))
    assert t.footnotes == {}
    for row in t.rows:
        for c in row.cells.values():
            assert not c.shaded and c.footnotes == []
            assert "shaded" not in c.to_dict()


def test_boxed_repeated_lines_do_not_make_a_table(tmp_path):
    page = Page()
    page.text(72, 70, "Table 8 - Invented Worked Example", bold=True)
    page.box(100, 100, 500, 220)
    for i in range(10):
        page.text(110, 106 + i * 11, "Same sentence in a plain box without rules")
    content = read_pdf(write_pdf(tmp_path / "t.pdf", [page]), "INV-1", "A")
    assert all(not is_degenerate(t) for t in content.tables)


def test_is_degenerate_filter():
    def table(texts):
        rows = [TableRow({}, {"V": Cell(s)}) for s in texts]  # 5020B Table 8: a box, one value column
        return Table("D", "A", "Table 8", "c", [], ["V"], rows)

    assert is_degenerate(table(["same"] * 3))
    assert not is_degenerate(table(["same"] * 2))
    assert not is_degenerate(table(["same", "same", "other"]))
    head = "Invented boxed example heading that repeats in every row of a box without inner rules, "
    assert is_degenerate(table([head + "1 2 3", head + "4 5 6", head + "7"]))
    assert not is_degenerate(table([head[:70] + "1", head[:70] + "2", head[:70] + "3"]))
    grouped = Table("D", "A", "Table 2", "c", ["Group", "Item"], ["V"],
                    [TableRow({"Group": head, "Item": f"{k}.1"}, {"V": Cell(f"text {k}")}) for k in range(3)])
    assert not is_degenerate(grouped)  # a long group label on every row is not a box
