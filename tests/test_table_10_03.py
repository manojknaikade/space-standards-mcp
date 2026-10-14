"""R5-T1003: column-0 group rows, no lone-value sub-rows, row-number column, rows carried over a page break.

Invented text; geometry follows the layouts measured on a real standard (column counts, rules, bold pattern,
line heights). PDFs come from tests/pdfgen.py."""

from __future__ import annotations

from pdfgen import Page, write_pdf

from spacestd.models import Cell, Table, TableRow
from spacestd.pdf_extract import merge_continuation, read_pdf


def _cell(page, x0, top, x1, bottom, lines=(), bold=False, dy=4.0, pitch=13.0, ys=None):
    """A ruled cell. Lines sit at top + dy + n * pitch, or at the explicit offsets `ys`."""
    page.box(x0, top, x1, bottom)
    for n, line in enumerate(lines):
        page.text(x0 + 3, top + (ys[n] if ys else dy + n * pitch), line, bold=bold)


def _read(tmp_path, pages):
    return read_pdf(write_pdf(tmp_path / "t.pdf", pages), doc_id="X-1").tables


# --------------------------------------------------------------------------- D1: column-0 group rows

XS5 = [60, 185, 245, 328, 407, 556]
HEAD5 = ["Test", "Clause", "Level", "Applicability", "Conditions"]


def _page5(caption, group, rows, notes=None):
    p = Page()
    if caption:
        p.text(60, 50, caption)
    top = 80
    for x0, x1, h in zip(XS5, XS5[1:], HEAD5):
        _cell(p, x0, top, x1, top + 30, [h], bold=True)
    bottom = top + 30
    if group:  # bold label in column 0, ONE empty cell across the other columns
        _cell(p, XS5[0], bottom, XS5[1], bottom + 14, [group], bold=True, dy=2)
        _cell(p, XS5[1], bottom, XS5[5], bottom + 14)
        bottom += 14
    for name, clause, app in rows:
        _cell(p, XS5[0], bottom, XS5[1], bottom + 14, [name], dy=2)
        _cell(p, XS5[1], bottom, XS5[2], bottom + 14, [clause], dy=2)
        _cell(p, XS5[2], bottom, XS5[3], bottom + 14)
        _cell(p, XS5[3], bottom, XS5[4], bottom + 14, [app], dy=2)
        _cell(p, XS5[4], bottom, XS5[5], bottom + 14)
        bottom += 14
    if notes:
        _cell(p, XS5[0], bottom, XS5[5], bottom + 30, notes)
    return p


def test_group_row_with_one_spanning_empty_cell(tmp_path):
    p = _page5("Table 6-1: Invented test matrix", "General", [("Wobble alignment", "9.8.1.1", "R"),
                                                           ("Fit check", "9.8.1.2", "R")])
    (t,) = _read(tmp_path, [p])
    assert t.label_columns[0] == "Group"
    assert (t.label_columns + t.value_columns)[1:] == ["Test", "Clause", "Level",
                                                       "Applicability", "Conditions"]
    assert [(r.labels["Group"], r.labels["Test"]) for r in t.rows] == [
        ("General", "Wobble alignment"), ("General", "Fit check")]


def test_group_row_continues_over_pages_and_notes_only_page(tmp_path):
    p1 = _page5("Table 6-1: Invented test matrix", "General", [("Wobble alignment", "9.8.1.1", "R")])
    p2 = _page5(None, "Mechanical", [("Spin check", "9.8.2.1", "R")])
    p3 = _page5(None, None, [], notes=["NOTE 1: Invented remark for the table."])
    (t,) = _read(tmp_path, [p1, p2, p3])
    assert [(r.labels["Group"], r.labels["Test"], r.page) for r in t.rows] == [
        ("General", "Wobble alignment", None), ("Mechanical", "Spin check", 2)]
    assert "Invented remark for the table." in " ".join(t.footnotes.values())


def test_group_row_with_separate_empty_cells_in_16_columns(tmp_path):
    xs = [40, 90, 130] + [170 + 35 * k for k in range(14)]  # 17 edges, 16 fine columns
    assert len(xs) == 17

    def page(caption, group, name):
        p = Page(width=700)
        if caption:
            p.text(40, 50, caption)
        _cell(p, xs[0], 80, xs[1], 120, ["Test"], bold=True)
        _cell(p, xs[1], 80, xs[2], 120, ["Ref"], bold=True)
        _cell(p, xs[2], 80, xs[3], 120, ["Lvl"], bold=True)
        _cell(p, xs[3], 80, xs[15], 100, ["Applicability versus types"], bold=True)
        for k, letter in enumerate("abcdefghijkl"):
            _cell(p, xs[3 + k], 100, xs[4 + k], 120, [letter], bold=True, dy=2)
        _cell(p, xs[15], 80, xs[16], 100, ["Notes"], bold=True)
        _cell(p, xs[15], 100, xs[16], 120)
        _cell(p, xs[0], 120, xs[1], 134, [group], bold=True, dy=2)
        for c in range(1, 16):  # fifteen separate empty cells
            _cell(p, xs[c], 120, xs[c + 1], 134)
        _cell(p, xs[0], 134, xs[1], 148, [name], dy=2)
        _cell(p, xs[1], 134, xs[2], 148, ["9.8.1.1"], dy=2)
        for c in range(2, 16):
            _cell(p, xs[c], 134, xs[c + 1], 148, ["R"] if c == 4 else [], dy=2)
        return p

    (t,) = _read(tmp_path, [page("Table 5-1: Invented matrix", "General", "Wobble"),
                            page(None, "Static", "Spin")])
    assert t.label_columns[:2] == ["Group", "Test"]
    assert all("General" not in c for c in t.label_columns + t.value_columns)
    assert [(r.labels["Group"], r.labels["Test"]) for r in t.rows] == [("General", "Wobble"), ("Static", "Spin")]


def test_group_row_in_two_columns(tmp_path):
    def page(caption, group, rows):
        p = Page()
        if caption:
            p.text(72, 50, caption)
        _cell(p, 72, 80, 250, 100, ["Test parameters"], bold=True)
        _cell(p, 250, 80, 450, 100, ["Test Input Tolerances"], bold=True)
        y = 100
        _cell(p, 72, y, 250, y + 20, [group], bold=True)
        _cell(p, 250, y, 450, y + 20)
        y += 20
        for a, b in rows:
            _cell(p, 72, y, 250, y + 20, [a])
            _cell(p, 250, y, 450, y + 20, [b])
            y += 20
        return p

    (t,) = _read(tmp_path, [page("Table 4-1: Invented parameters", "5. Sine sweep", [("Rate", "2 dB")]),
                            page(None, "6. Random run", [("Duration", "120 s"), ("Axis", "3 dB")])])
    assert t.value_columns[-1] == "Test Input Tolerances" and "Test parameters" in (t.label_columns + t.value_columns)
    assert [(r.labels["Group"], r.page) for r in t.rows] == [("5. Sine sweep", None), ("6. Random run", 2),
                                                             ("6. Random run", 2)]


def test_bold_label_with_a_neighbour_value_is_not_a_group(tmp_path):
    p = Page()
    p.text(72, 50, "Table 4-2: Invented")
    _cell(p, 72, 80, 250, 100, ["Part"], bold=True)
    _cell(p, 250, 80, 450, 100, ["Load"], bold=True)
    _cell(p, 72, 100, 250, 120, ["Widget"], bold=True)
    _cell(p, 250, 100, 450, 120, ["2,5"])
    (t,) = _read(tmp_path, [p])
    assert t.label_columns == ["Part"] and [r.labels["Part"] for r in t.rows] == ["Widget"]


# --------------------------------------------------------------------------- D2 / D3: six-column tables

XS6 = [50, 78, 174, 383, 545, 635, 780]
HEAD6 = ["No", "Test", "Levels", "Duration", "Number", "NOTES"]


def _page6(caption, rows):
    """rows: (top, bottom, [(lines, bold, line offsets) per column])."""
    p = Page(width=842)
    if caption:
        p.text(50, 50, caption)
    for x0, x1, h in zip(XS6, XS6[1:], HEAD6):
        _cell(p, x0, 73, x1, 111, [h], bold=True)
    for top, bottom, cols in rows:
        for x0, x1, (lines, bold, ys) in zip(XS6, XS6[1:], cols):
            _cell(p, x0, top, x1, bottom, lines, bold=bold, ys=ys)
    return p


ROW1 = (111.0, 161.0, [(["1"], True, [13.6]), (["Visual"], True, [13.6]), (["20 g"], False, [13.0]),
                       (["10 s"], False, [13.0]), (["1"], False, [13.0]), ([], False, None)])
# measured shape of a split row: lone values at different heights, no cell stacks values
ROW7 = (161.0, 210.0, [(["7"], True, [13.6]), (["Wobbly", "shaking"], True, [13.6, 28.4]),
                       (["Low level sine", "survey with", "notches"], False, [12.8, 30.2, 43.7]),
                       (["sweep at 2 Oct/min,", "5 Hz - 140 Hz"], False, [12.8, 30.2]),
                       (["sine test", "required"], False, [12.8, 30.2]), ([], False, None)])


def test_lone_values_at_different_heights_are_one_row(tmp_path):
    (t,) = _read(tmp_path, [_page6("Table 5-2: Invented tests", [ROW1, ROW7])])
    assert len(t.rows) == 2
    # the row number is a label column; so is 'Test' (the first column with a value token is 'Levels')
    assert t.label_columns == ["No", "Test"] and t.value_columns == ["Levels", "Duration", "Number",
                                                                     "NOTES"]
    assert [(r.labels["No"], r.labels["Test"]) for r in t.rows] == [("1", "Visual"), ("7", "Wobbly shaking")]
    assert t.rows[1].cells["Duration"].text == "sweep at 2 Oct/min, 5 Hz - 140 Hz"


def test_lone_values_without_row_numbers_one_row(tmp_path):
    p = Page()
    p.text(72, 50, "Table 3-1: Invented")
    for x0, x1, h in [(72, 172, "Part"), (172, 272, "Load"), (272, 372, "Time")]:
        _cell(p, x0, 80, x1, 100, [h], bold=True)
    _cell(p, 72, 100, 172, 140, ["Spin", "check"], ys=[14, 28])
    _cell(p, 172, 100, 272, 140, ["5 N"], ys=[14])
    _cell(p, 272, 100, 372, 140, ["10 s"], ys=[28])
    (t,) = _read(tmp_path, [p])
    assert [(r.labels["Part"], r.cells["Load"].text, r.cells["Time"].text) for r in t.rows] == [
        ("Spin check", "5 N", "10 s")]


def test_row_number_column_is_label_only_for_bare_numbers(tmp_path):
    p = Page()
    p.text(72, 50, "Table 3-2: Invented")
    for x0, x1, h in [(72, 172, "Item"), (172, 272, "Load")]:
        _cell(p, x0, 80, x1, 100, [h], bold=True)
    _cell(p, 72, 100, 172, 120, ["2 bolts"])  # not a bare row number
    _cell(p, 172, 100, 272, 120, ["5 N"])
    (t,) = _read(tmp_path, [p])
    assert t.label_columns == [] and t.value_columns == ["Item", "Load"]


def test_row_carried_over_a_page_break(tmp_path):
    first = (161.0, 700.0, [(["7"], True, [13.6]), (["Wobbly", "shaking"], True, [13.6, 28.4]),
                            (["sine"], False, [13.0]), (["sweep at"], False, [13.0]), ([], False, None),
                            ([], False, None)])
    rest = (111.0, 300.0, [([], False, None), ([], False, None), ([], False, None),
                           (["2 Oct/min,", "5 Hz - 140 Hz", "then hold", "5 min", "dwell", "end"], False,
                            [13, 30, 47, 64, 81, 98]),
                           ([], False, None), (["Remark one", "Remark two"], False, [13, 30])])
    ts = _read(tmp_path, [_page6("Table 5-4: Invented", [ROW1, first]), _page6(None, [rest])])
    assert len(ts) == 1
    t = ts[0]
    assert len(t.rows) == 2 and t.rows[1].labels["No"] == "7"
    assert t.rows[1].cells["Duration"].text.startswith("sweep at 2 Oct/min, 5 Hz - 140 Hz then hold")
    assert t.rows[1].cells["NOTES"].text == "Remark one Remark two"


def _row(no, **cells):
    return TableRow({"No": no, "Test": "t"}, {k: Cell(text=v) for k, v in cells.items()})


def test_merge_continuation_carries_only_leading_unlabelled_rows():
    # measured 10-03C Table 5-4 p. 59: No, Test and Levels empty, Duration and NOTES continue row 7
    base = Table("X-1", "", "Table 1", "", ["No", "Test"], ["Levels", "Duration", "NOTES"],
                 [_row("6", Levels="L6", Duration="a", NOTES=""), _row("7", Levels="L7", Duration="b", NOTES="n")])
    cont = Table("X-1", "", "Table 1", "", ["No", "Test"], ["Levels", "Duration", "NOTES"],
                 [TableRow({"No": "", "Test": ""}, {"Levels": Cell(text=""), "Duration": Cell(text="c"),
                                                    "NOTES": Cell(text="m")}),
                  _row("8", Levels="L8", Duration="d", NOTES=""),
                  TableRow({"No": "", "Test": ""}, {"Levels": Cell(text=""), "Duration": Cell(text="e"),
                                                    "NOTES": Cell(text="")})])
    merge_continuation(base, cont, 3)
    assert [r.labels["No"] for r in base.rows] == ["6", "7", "8", ""]  # only the leading one is carried
    assert base.rows[1].cells["Duration"].text == "b c" and base.rows[1].cells["NOTES"].text == "n m"
    assert base.rows[1].page is None


def test_merge_continuation_keeps_unlabelled_rows_that_start_a_value():
    # 5019A Tables 4-7: the label column is printed on the first page only; continuation rows have empty
    # labels but their own clause number in the first value column: they are rows, not carried text
    base = Table("X-1", "", "Table 5", "", ["Description"], ["Clause", "Text"],
                 [TableRow({"Description": "Invented group"}, {"Clause": Cell(text="7.2"), "Text": Cell(text="x")})])
    cont = Table("X-1", "", "Table 5", "", ["Description"], ["Clause", "Text"],
                 [TableRow({"Description": ""}, {"Clause": Cell(text=""), "Text": Cell(text="g. tail")}),
                  TableRow({"Description": ""}, {"Clause": Cell(text="7.3"), "Text": Cell(text="y")})])
    merge_continuation(base, cont, 2)
    assert [r.cells["Clause"].text for r in base.rows] == ["7.2", "7.3"]
    assert base.rows[0].cells["Text"].text == "x g. tail"


def test_merge_continuation_without_label_columns_adds_rows():
    base = Table("X-1", "", "Table 1", "", [], ["A"], [TableRow({}, {"A": Cell(text="1")})])
    cont = Table("X-1", "", "Table 1", "", [], ["A"], [TableRow({}, {"A": Cell(text="2")})])
    merge_continuation(base, cont, 2)
    assert [r.cells["A"].text for r in base.rows] == ["1", "2"]


# --------------------------------------------------------------------------- integration fixes (round 5)

def test_continuation_with_a_different_label_split_is_rekeyed_by_position():
    # 10-03C Table 6-1 p. 89: an empty column on the continuation page turns 'Clause' into a label there
    base = Table("X-1", "", "Table 1", "", ["Group", "Test"], ["Clause", "Level"],
                 [TableRow({"Group": "G", "Test": "t1"}, {"Clause": Cell("6.1"), "Level": Cell("L")})])
    cont = Table("X-1", "", "Table 1", "", ["Test", "Clause"], ["Level"],
                 [TableRow({"Test": "t2", "Clause": "6.2"}, {"Level": Cell("")})])
    merge_continuation(base, cont, 2)
    r = base.rows[-1]
    assert list(r.labels) == ["Group", "Test"] and r.labels["Test"] == "t2"
    assert list(r.cells) == ["Clause", "Level"] and r.cells["Clause"].text == "6.2"
    assert r.labels["Group"] == "G"  # still under the last group


def test_row_number_table_labels_are_number_and_next_column(tmp_path):
    # 10-03C Tables 5-2 ...: 'No' | 'Test' label the rows; 'Levels' is a value column although no line in
    # it starts with a number
    xs = [50, 80, 170, 330, 450]
    p = Page()
    p.text(50, 50, "Table 1: Invented test levels")
    for x0, x1, h in zip(xs, xs[1:], ["No", "Test", "Levels", "Duration"]):
        _cell(p, x0, 80, x1, 100, [h], bold=True)
    for n, (test, lev, dur) in enumerate([("Wobble", "Expected spectrum", "2 minutes"),
                                         ("Shake", "Limit spectrum", "As needed")]):
        top = 100 + 30 * n
        for x0, x1, txt in zip(xs, xs[1:], [str(n + 1), test, lev, dur]):
            _cell(p, x0, top, x1, top + 30, [txt])
    t = _read(tmp_path, [p])[0]
    assert t.label_columns == ["No", "Test"] and t.value_columns == ["Levels", "Duration"]
    assert [r.labels["No"] for r in t.rows] == ["1", "2"]


def test_bottom_key_block_beside_a_legend_cell_is_footnotes(tmp_path):
    # 10-03C Table 5-3 p. 56: under the matrix a bold heading cell and a cell of 'a ... d ...' key entries
    # span all but the last column; the last column holds 'Key' and 'R Required'
    xs = [40, 140, 160, 180, 300]
    p = Page()
    p.text(40, 50, "Table 1: Invented applicability")
    for x0, x1, h in zip(xs, xs[1:], ["Test", "a", "b", "Notes"]):
        _cell(p, x0, 80, x1, 100, [h], bold=True)
    for n, (test, a, b) in enumerate([("Wobble", "R", "X"), ("Shake", "X", "R")]):
        top = 100 + 16 * n
        for x0, x1, txt in zip(xs, xs[1:], [test, a, b, ""]):
            _cell(p, x0, top, x1, top + 16, [txt] if txt else [])
    _cell(p, xs[0], 132, xs[3], 148, ["Kinds of widget"], bold=True)
    _cell(p, xs[3], 132, xs[4], 148, ["Key"])
    _cell(p, xs[0], 148, xs[3], 166, ["a Alpha widget b Beta widget"])
    _cell(p, xs[3], 148, xs[4], 166, ["R Required"])
    t = _read(tmp_path, [p])[0]
    assert [r.labels.get("Test") for r in t.rows] == ["Wobble", "Shake"]
    assert t.footnotes.get("a") == "Alpha widget" and t.footnotes.get("b") == "Beta widget"


def test_group_bar_cut_into_cells_by_fine_columns(tmp_path):
    # 7002B Table 1: '(4)' marks in some label cells add column edges, so the bold section bar is three
    # cells 'EMI' | '/EMC' | 'TESTS' with one empty cell over the value columns
    xs = [72, 98, 124, 300, 377]
    p = Page()
    p.text(72, 50, "Table 1: Invented test matrix")
    _cell(p, xs[0], 80, xs[3], 100, ["Test"], bold=True)
    _cell(p, xs[3], 80, xs[4], 100, ["Unit"], bold=True)
    _cell(p, xs[0], 100, xs[2], 116, ["Wobble cycle"])
    _cell(p, xs[2], 100, xs[3], 116, ["(4)"])
    _cell(p, xs[3], 100, xs[4], 116, ["2"])
    _cell(p, xs[0], 116, xs[1], 132, ["ZAP"], bold=True)
    _cell(p, xs[1], 116, xs[2], 132, ["/ZIP"], bold=True)
    _cell(p, xs[2], 116, xs[3], 132, ["TESTS"], bold=True)
    _cell(p, xs[3], 116, xs[4], 132, [])
    _cell(p, xs[0], 132, xs[3], 148, ["Zap emissions"])
    _cell(p, xs[3], 132, xs[4], 148, ["7"])
    t = _read(tmp_path, [p])[0]
    rows = {list(r.labels.values())[-1]: r for r in t.rows}
    assert "ZAP /ZIP TESTS" not in " ".join(rows)  # not a data row
    assert rows["Zap emissions"].labels["Group"] == "ZAP /ZIP TESTS"


def test_numbered_group_row_with_roman_sub_labels_is_a_group(tmp_path):
    # 10-03C Table 4-1: a spanning row '1. Temperature' (bold) + 'Low High' (roman, same line) is a group
    # heading, not a data row repeated in every column
    xs = [72, 300, 500]
    p = Page()
    p.text(72, 50, "Table 4-1: Invented tolerances")
    _cell(p, xs[0], 80, xs[1], 100, ["Parameter"], bold=True)
    _cell(p, xs[1], 80, xs[2], 100, ["Tolerance"], bold=True)
    p.box(xs[0], 100, xs[2], 118)
    p.text(75, 104, "1. Wobble", bold=True)
    p.text(175, 104, "Low   High")
    _cell(p, xs[0], 118, xs[1], 136, ["5 K and above"])
    _cell(p, xs[1], 118, xs[2], 136, ["+1/-2 K"])
    _cell(p, xs[0], 136, xs[1], 154, ["4 K or less"])
    _cell(p, xs[1], 136, xs[2], 154, ["3 K"])
    _cell(p, xs[0], 154, xs[1], 172, ["2. Fuzz"], bold=True)
    _cell(p, xs[1], 154, xs[2], 172, ["10 %"])
    t = _read(tmp_path, [p])[0]
    assert t.label_columns == ["Group"]
    assert [(r.labels["Group"], r.cells["Parameter"].text) for r in t.rows] == [
        ("1. Wobble Low High", "5 K and above"), ("1. Wobble Low High", "4 K or less"), ("2. Fuzz", "2. Fuzz")]


def test_group_label_in_the_header_band_is_a_group_not_a_column_name(tmp_path):
    # 7002B Table 1: the bold group label 'ZAP TESTS' is printed on the header's line, in a cell below
    # the empty top-left header cell; the value headers are tall cells reaching down beside it
    xs = [72, 200, 280, 360]
    p = Page()
    p.text(72, 50, "Table 1: Invented test matrix")
    _cell(p, xs[0], 80, xs[1], 96)
    _cell(p, xs[1], 80, xs[2], 124, ["Unit"], bold=True, ys=[38])
    _cell(p, xs[2], 80, xs[3], 124, ["System"], bold=True, ys=[38])
    _cell(p, xs[0], 96, xs[1], 124, ["ZAP TESTS"], bold=True, ys=[22])
    for k, (name, a, b) in enumerate([("Wobble", "1", "2"), ("Shake", "", "3")]):
        top = 124 + 16 * k
        _cell(p, xs[0], top, xs[1], top + 16, [name], dy=2)
        _cell(p, xs[1], top, xs[2], top + 16, [a], dy=2)
        _cell(p, xs[2], top, xs[3], top + 16, [b], dy=2)
    t = _read(tmp_path, [p])[0]
    assert t.value_columns == ["Unit", "System"]
    assert "ZAP TESTS" not in t.label_columns + t.value_columns
    assert [(r.labels["Group"], r.cells["Unit"].text) for r in t.rows] == [("ZAP TESTS", "1"), ("ZAP TESTS", "")]
