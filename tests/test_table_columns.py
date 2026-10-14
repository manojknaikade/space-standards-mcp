"""Table columns and stacked sub-rows (H17): repeated and split columns, stacked lines, wrapped labels.

PDFs are drawn with tests/pdfgen.py; all text is invented.
"""

from pdfgen import Page, write_pdf

from spacestd.pdf_extract import read_pdf


def _read(tmp_path, page):
    (t,) = read_pdf(write_pdf(tmp_path / "t.pdf", [page]), doc_id="X-1").tables
    return t


def _frame(page, xs, ys, heads, caption="Table 9-1: Invented layout"):
    page.text(72, 80, caption, size=11, bold=True)
    page.grid(xs, ys)
    for x, s in zip(xs, heads):
        if s:
            page.text(x + 4, ys[0] + 5, s, bold=True)


def _fill(page, x, top, lines, step=12):
    for k, s in enumerate(lines):
        page.text(x + 4, top + k * step, s)


def test_repeated_header_pattern_is_unfolded(tmp_path):
    xs = [72, 132, 192, 252, 312, 372, 432, 492, 552]
    ys = [100, 120, 140, 160, 180]
    page = Page()
    _frame(page, xs, ys, ["m", "s", "m", "s", "m", "s", "m", "s"])
    for b in range(4):  # block by block: rows 1-3 of the first pair, then the second pair ...
        for r in range(3):
            page.text(xs[2 * b] + 4, ys[r + 1] + 5, f"{b + 1}{r + 1}1")
            page.text(xs[2 * b + 1] + 4, ys[r + 1] + 5, f"{b + 1}{r + 1}2")
    t = _read(tmp_path, page)
    assert t.label_columns == [] and t.value_columns == ["m", "s"]
    assert [(r.cells["m"].text, r.cells["s"].text) for r in t.rows] == [
        (f"{b + 1}{r + 1}1", f"{b + 1}{r + 1}2") for b in range(4) for r in range(3)]


def test_duplicate_column_names_get_a_suffix(tmp_path):
    xs = [72, 200, 300, 400, 500]
    ys = [100, 120, 140, 160]
    page = Page()
    _frame(page, xs, ys, ["Item", "Load", "Mass", "Load"])
    for r, row in enumerate([("a", "1,5", "7", "2,5"), ("b", "1,6", "8", "2,6")], 1):
        for x, s in zip(xs, row):
            page.text(x + 4, ys[r] + 5, s)
    t = _read(tmp_path, page)
    assert t.value_columns == ["Load", "Mass", "Load (2)"]
    assert [r.cells["Load (2)"].text for r in t.rows] == ["2,5", "2,6"]


def _sums_table(page, rows):
    """Header: empty cell + one bold 'Sums' cell over two fine columns; the sub-columns have no header.
    A row whose second entry is None is one cell spanning both sub-columns (drawn as the last row)."""
    x0, x1, x2, x3 = 72, 172, 292, 412
    page.text(72, 80, "Table 9-2: Invented sums", size=11, bold=True)
    ys = [100, 120] + [120 + 20 * (k + 1) for k in range(len(rows))]
    for y in ys:
        page.hline(y, x0, x3)
    for x in (x0, x1, x3):
        page.vline(x, ys[0], ys[-1])
    page.vline(x2, ys[1], ys[-2])  # the last row has no middle rule
    page.text(x1 + 4, ys[0] + 5, "Sums", bold=True)
    for k, (label, a, b) in enumerate(rows):
        top = ys[k + 1] + 5
        page.text(x0 + 4, top, label)
        if a:
            page.text(x1 + 4, top, a)
        if b:
            page.text(x2 + 4, top, b)


def test_unlabelled_sub_columns_are_split(tmp_path):
    page = Page()
    _sums_table(page, [("A", "40x3 = 120", "40x2 = 80"), ("B", "20x1 = 20", ""), ("C", "7x2 = 14", "7x2 = 14"),
                       ("D", "9x9 = 81", "")])
    t = _read(tmp_path, page)
    assert t.value_columns == ["Sums (1)", "Sums (2)"]
    got = [(r.cells["Sums (1)"].text, r.cells["Sums (2)"].text) for r in t.rows]
    assert got == [("40x3 = 120", "40x2 = 80"), ("20x1 = 20", ""), ("7x2 = 14", "7x2 = 14"),
                   ("9x9 = 81", "9x9 = 81")]


def _stack_table(page, heads, columns, xs, step=12):
    n = max(len(c) for c in columns)
    ys = [100, 120, 120 + 10 + step * n]
    _frame(page, xs, ys, heads, "Table 9-3: Invented stacks")
    for x, lines in zip(xs, columns):
        _fill(page, x, ys[1] + 5, lines, step)


def test_stacked_sub_rows_in_every_column(tmp_path):
    pct = [f"{5 + k}%" for k in range(10)] + ["Total"]
    cols = [pct] + [[str(10 * c + k) for k in range(10)] + [str(1000 + c)] for c in range(1, 5)]
    page = Page()
    _stack_table(page, ["Share", "A", "B", "C", "D"], cols, xs=[72, 152, 232, 312, 392, 472])
    t = _read(tmp_path, page)
    assert len(t.rows) == 11
    assert t.rows[0].cells["A"].text == "10" and t.rows[10].cells["D"].text == "1004"
    assert [r.labels["Share"] for r in t.rows] == pct


def test_two_columns_stack_seven_lines(tmp_path):
    page = Page()
    _stack_table(page, ["Item", "Freq", "Level"],
                 [["Band"], [str(20 * (k + 1)) for k in range(7)], [str(100 + k) for k in range(7)]],
                 xs=[72, 202, 302, 402])
    t = _read(tmp_path, page)
    assert len(t.rows) == 7
    assert [r.cells["Freq"].text for r in t.rows] == [str(20 * (k + 1)) for k in range(7)]
    assert all(r.labels["Item"] == "Band" for r in t.rows)  # the single line spans every sub-row
    assert [r.cells["Level"].text for r in t.rows] == [str(100 + k) for k in range(7)]


def test_three_sub_rows_with_fill_down(tmp_path):
    page = Page()
    cols = [["Flat face"], ["0.4 <= w <= 1.6", "w > 1.6"], ["Full", "Part"], ["w", "0.7", "1.6"], ["1.6", "3.1", "1.6"]]
    _stack_table(page, ["Shape", "Width", "Fill", "P", "Q"], cols, xs=[72, 152, 292, 362, 442, 522])
    t = _read(tmp_path, page)
    assert len(t.rows) == 3
    assert [r.cells["Width"].text for r in t.rows] == ["0.4 <= w <= 1.6", "w > 1.6", "w > 1.6"]
    assert [r.cells["Fill"].text for r in t.rows] == ["Full", "Part", "Part"]
    assert all(r.labels["Shape"] == "Flat face" for r in t.rows)
    assert [r.cells["Q"].text for r in t.rows] == ["1.6", "3.1", "1.6"]


def test_wrapped_sub_row_label_centred_on_its_value(tmp_path):
    page = Page()
    xs = [72, 252, 352, 452]
    ys = [100, 120, 220]
    _frame(page, xs, ys, ["Case", "P", "Q"], "Table 9-4: Invented wrapped label")
    for y, s in zip([136, 154, 172], ["Alpha", "Beta", "Gamma"]):
        page.text(xs[0] + 4, y - 3.6, s)
    page.text(xs[0] + 4, 190 - 3.6, "Delta part one")
    page.text(xs[0] + 4, 203 - 3.6, "and part two")
    for x, base in ((xs[1], 10), (xs[2], 20)):
        for y, k in zip([136, 154, 172, 197], range(4)):
            page.text(x + 4, y - 3.6, str(base + k))
    t = _read(tmp_path, page)
    assert [r.labels["Case"] for r in t.rows] == ["Alpha", "Beta", "Gamma", "Delta part one and part two"]
    assert [r.cells["P"].text for r in t.rows] == ["10", "11", "12", "13"]


def test_one_stacked_cell_alone_stays_one_row(tmp_path):
    page = Page()
    xs = [72, 202, 302, 402]
    ys = [100, 120, 180]
    _frame(page, xs, ys, ["Case", "P", "Q"], "Table 9-5: Invented single stack")
    page.text(xs[0] + 4, 130, "Joint")
    for k in range(3):
        page.text(xs[1] + 4, 128 + 12 * k, "1,4")
    page.text(xs[2] + 4, 130, "2,0")
    t = _read(tmp_path, page)
    assert len(t.rows) == 1


def test_two_wrapped_text_columns_stay_one_row(tmp_path):
    page = Page()
    xs = [72, 252, 432, 552]
    ys = [100, 120, 180]
    _frame(page, xs, ys, ["Left", "Right", "Ref"], "Table 9-6: Invented text columns")
    _fill(page, xs[0], 128, ["Invented text that", "wraps twice here", "and a third"])
    _fill(page, xs[1], 128, ["Other words that", "also wrap here", "and again"])
    page.text(xs[2] + 4, 140, "7")
    t = _read(tmp_path, page)
    assert len(t.rows) == 1


def test_wrapped_labels_beside_two_values_make_no_anchors(tmp_path):
    page = Page()
    xs = [72, 152, 272, 352, 432]
    ys = [100, 120, 200]
    _frame(page, xs, ys, ["Group", "Case", "P", "Q"], "Table 9-7: Invented wrapped groups")
    _fill(page, xs[0], 150, ["Storage and", "widget loads"], 13)
    for y, s in zip([130, 150, 163, 181], ["Widget", "-local transport and", "storage loads", "-other transport loads"]):
        page.text(xs[1] + 4, y, s)
    page.text(xs[2] + 4, 150, "2")
    page.text(xs[2] + 4, 181, "1,4")
    page.text(xs[3] + 4, 157, "N/A")
    t = _read(tmp_path, page)
    assert [r.cells["P"].text for r in t.rows] == ["2", "1,4"]
