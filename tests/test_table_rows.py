"""H17 T1: trailing notes blocks and group-heading rows (invented text, PDFs from tests/pdfgen.py)."""

from __future__ import annotations

from pdfgen import Page, write_pdf

from spacestd.pdf_extract import read_pdf

LH = 12  # line pitch inside a cell


def _table(tmp_path, xs, rows, caption="Table 9-9: Invented widget table"):
    """rows: (cuts, [(first column, [lines], bold)]); `cuts` are the column edges (indices into xs) drawn
    as vertical rules in that grid row, so a cell without inner cuts spans the row. bold=True bolds every
    line, bold="first" only the first line. Row height follows the longest cell."""
    page = Page()
    page.text(xs[0], 60, caption)
    ys = [80.0]
    for _, texts in rows:
        n = max([len(lines) for _, lines, _ in texts] + [1])
        ys.append(ys[-1] + 6 + LH * n)
    for y in ys:
        page.hline(y, xs[0], xs[-1])
    for r, (cuts, texts) in enumerate(rows):
        for k in cuts:
            page.vline(xs[k], ys[r], ys[r + 1])
        for col, lines, bold in texts:
            for n, line in enumerate(lines):
                page.text(xs[col] + 4, ys[r] + 4 + LH * n, line, bold=bold is True or (bold == "first" and n == 0))
    (t,) = read_pdf(write_pdf(tmp_path / "t.pdf", [page]), doc_id="X-1").tables
    return t


XS6 = [72, 150, 220, 290, 360, 430, 500]
ALL6 = list(range(7))
HEAD6 = (ALL6, [(0, ["Item"], True), (1, ["Mass"], True), (2, ["Load"], True),
                (3, ["Span"], True), (4, ["Depth"], True), (5, ["Skew"], True)])


def _row6(name):
    return (ALL6, [(0, [name], False), (1, ["1,25"], False), (2, ["2,5"], False),
                   (3, ["3,5"], False), (4, ["4,5"], False), (5, ["5,5"], False)])


def _notes(tmp_path, lines, cuts=(0, 6)):
    return _table(tmp_path, XS6, [HEAD6, _row6("Widget"), (list(cuts), [(0, lines, False)])])


def test_paren_markers_glued_or_spaced(tmp_path):
    t = _notes(tmp_path, ["(1)For widgets with a spare.", "(2) Sprocket drift is small."])
    assert t.footnotes == {"1": "For widgets with a spare.", "2": "Sprocket drift is small."}
    assert len(t.rows) == 1 and t.rows[0].labels == {"Item": "Widget"}


def test_digit_markers_with_space_and_continuation(tmp_path):
    t = _notes(tmp_path, ["1 Bays are listed in", "the usual order.", "2 Where the paint peels."])
    assert t.footnotes == {"1": "Bays are listed in the usual order.", "2": "Where the paint peels."}
    assert len(t.rows) == 1


def test_legend_line_before_numbered_notes_and_dash_legend(tmp_path):
    t = _notes(tmp_path, ["R=Required, D=Desired, not required", "(1) Applies to spares."])
    assert t.footnotes == {"Key R": "Required", "Key D": "Desired, not required", "1": "Applies to spares."}
    t = _notes(tmp_path, ["Legend:", "R - Required check. Always.", "AN - Check as needed."])
    assert t.footnotes == {"Key R": "Required check. Always.", "Key AN": "Check as needed."}
    assert len(t.rows) == 1


def test_heading_with_labelled_lines_and_bullets(tmp_path):
    t = _notes(tmp_path, ["NOTES:", "case 1: The first widget.", "case 2: The second widget."])
    assert t.footnotes == {"case 1": "The first widget.", "case 2": "The second widget."}
    t = _notes(tmp_path, ["Assumptions:", "· Bays are dry.", "· Paint is blue."])
    assert t.footnotes == {"Assumptions": "· Bays are dry. · Paint is blue."}
    assert len(t.rows) == 1


def test_notes_cell_not_spanning_every_column(tmp_path):
    t = _notes(tmp_path, ["R=Required, D=Desired", "(1) Applies to spares."], cuts=(0, 4, 5, 6))
    assert t.footnotes == {"Key R": "Required", "Key D": "Desired", "1": "Applies to spares."}
    assert len(t.rows) == 1


def test_marker_like_text_inside_cells_is_unchanged(tmp_path):
    t = _table(tmp_path, XS6, [HEAD6, _row6("Widget(1,2)"), _row6("count(1)")])
    assert [r.labels["Item"] for r in t.rows] == ["Widget(1,2)", "count(1)"] and not t.footnotes


def test_last_data_row_starting_with_a_number_stays_a_row(tmp_path):
    t = _table(tmp_path, XS6, [HEAD6, _row6("Widget"), _row6("2 x 4 widgets")])
    assert len(t.rows) == 2 and not t.footnotes  # a data row, not a notes block


def test_full_width_last_row_without_marker_stays_a_row(tmp_path):
    t = _table(tmp_path, XS6, [HEAD6, _row6("Widget"), ([0, 6], [(0, ["Totals include spares"], False)])])
    assert len(t.rows) == 2 and not t.footnotes


XS5 = [72, 160, 240, 320, 400, 480]
ALL5 = list(range(6))
HEAD5 = (ALL5, [(0, ["Location"], True), (1, ["Thickness"], True), (2, ["Type"], True),
                (3, ["Size a"], True), (4, ["Size c"], True)])


def _row5(name):
    return (ALL5, [(0, [name], False), (1, ["1,5"], False), (2, ["Edge"], False),
                   (3, ["2,5"], False), (4, ["3,5"], False)])


def test_group_headings_five_columns_with_qualifier(tmp_path):
    rows = [HEAD5, ([0, 5], [(0, ["Widget NDE"], True)]), _row5("Top"), _row5("Side"),
            ([0, 5], [(0, ["Sprocket NDE", "within the bay"], "first")]), _row5("Rim")]
    t = _table(tmp_path, XS5, rows)
    assert t.label_columns == ["Group", "Location"]
    assert t.value_columns == ["Thickness", "Type", "Size a", "Size c"]
    assert [(r.labels["Group"], r.labels["Location"]) for r in t.rows] == [
        ("Widget NDE", "Top"), ("Widget NDE", "Side"), ("Sprocket NDE within the bay", "Rim")]


def test_group_headings_two_columns_and_numbered(tmp_path):
    xs = [72, 200, 330]

    def data(a, b):
        return ([0, 1, 2], [(0, [a], False), (1, [b], False)])

    head = ([0, 1, 2], [(0, ["Old paint"], True), (1, ["New paint"], True)])
    rows = [head, ([0, 2], [(0, ["1. Widget mass"], True)]), data("1,5", "1,6"),
            ([0, 2], [(0, ["2. Widget balance"], True)]), data("2,5", "2,6")]
    t = _table(tmp_path, xs, rows)
    assert t.label_columns == ["Group"] and t.value_columns == ["Old paint", "New paint"]
    assert [(r.labels["Group"], r.cells["Old paint"].value) for r in t.rows] == [
        ("1. Widget mass", 1.5), ("2. Widget balance", 2.5)]


def test_bold_full_width_notes_row_is_not_a_group(tmp_path):
    t = _table(tmp_path, XS6, [HEAD6, _row6("Widget"), ([0, 6], [(0, ["NOTES:", "(1) Dry bays."], True)])])
    assert t.label_columns == ["Item"] and t.footnotes == {"1": "Dry bays."}


def test_empty_bold_column_before_values_stays_a_value_column(tmp_path):
    xs = [72, 160, 240, 320, 400]
    head = ([0, 1, 2, 3, 4], [(0, ["Item"], True), (1, ["FOSY"], True), (2, ["Load"], True), (3, ["Span"], True)])
    # the second row's cell starts in the empty column and reaches into a value column
    one = ([0, 1, 2, 3, 4], [(0, ["Widget"], False), (2, ["2,5"], False), (3, ["3,5"], False)])
    two = ([0, 1, 3, 4], [(0, ["Sprocket"], False), (1, ["See above"], False), (3, ["4,5"], False)])
    t = _table(tmp_path, xs, [head, one, two])
    assert t.label_columns == ["Item"] and t.value_columns == ["FOSY", "Load", "Span"]


def test_heading_block_digit_led_wrapped_line_continues_the_note(tmp_path):
    t = _notes(tmp_path, ["Assumptions:", "· Burn lasts about", "15 seconds during the burn.", "· The next phase."])
    assert t.footnotes == {"Assumptions": "· Burn lasts about 15 seconds during the burn. · The next phase."}
    t = _notes(tmp_path, ["NOTES:", "case 1: The first widget,", "15 seconds long.", "case 2: The second."])
    assert t.footnotes == {"case 1": "The first widget, 15 seconds long.", "case 2": "The second."}


def test_numbered_group_with_values_beside_it_is_its_own_group(tmp_path):
    xs = [72, 170, 260, 350]
    al = [0, 1, 2, 3]
    head = (al, [(0, ["Part"], True), (1, ["Old paint"], True), (2, ["New paint"], True)])
    rows = [head, ([0, 3], [(0, ["1. Widget mass"], True)]),
            (al, [(0, ["Top"], False), (1, ["1,5"], False), (2, ["1,6"], False)]),
            (al, [(0, ["2. Widget leak"], True), (2, ["2,6"], False)]),
            ([0, 3], [(0, ["3. Widget spin"], True)]),
            (al, [(0, ["Side"], False), (1, ["3,5"], False), (2, ["3,6"], False)])]
    t = _table(tmp_path, xs, rows)
    assert [(r.labels["Group"], r.labels["Part"], r.cells["Old paint"].text, r.cells["New paint"].text)
            for r in t.rows] == [("1. Widget mass", "Top", "1,5", "1,6"), ("2. Widget leak", "", "", "2,6"),
                                 ("3. Widget spin", "Side", "3,5", "3,6")]


def test_merge_continuation_fills_empty_group_from_the_base():
    from spacestd.models import Cell, Table, TableRow
    from spacestd.pdf_extract import merge_continuation

    def row(group):
        return TableRow({"Group": group, "Item": "x"}, {"V": Cell(text="1", value=1.0)})

    base = Table("X-1", "", "Table 1", "", ["Group", "Item"], ["V"], [row(""), row("1. Widget mass")])
    cont = Table("X-1", "", "Table 1", "", ["Group", "Item"], ["V"], [row(""), row("2. Widget balance"), row("")])
    merge_continuation(base, cont, 2)
    assert [r.labels["Group"] for r in base.rows] == ["", "1. Widget mass", "1. Widget mass", "2. Widget balance",
                                                      "2. Widget balance"]
