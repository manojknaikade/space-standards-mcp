"""Table logic on invented inputs: superscript footnotes, continuation pages, duplicate IDs."""
from spacestd.models import Cell, Table, TableRow
from spacestd.pdf_extract import (
    Line,
    _split_size_runs,
    continues,
    dedupe_tables,
    header_signature,
    is_page_top,
    merge_continuation,
    normalise,
    parse_cell,
    trailing_caption,
)


def _ch(text, x0, size=10.0, top=0.0):
    return {"text": text, "x0": x0, "x1": x0 + 0.6 * size, "top": top, "bottom": top + size, "size": size,
            "fontname": "Body-Roman", "upright": True}


def _cell_text(main, sup):
    chars = [_ch(c, 10 + 5 * i) for i, c in enumerate(main)]
    chars += [_ch(c, 10 + 5 * len(main) + 3 * i, 6.5, -2) for i, c in enumerate(sup)]
    return normalise(_split_size_runs(main + sup, chars))


def test_superscript_not_fused_into_value():
    for main, sup, value, notes in [("1.10", "5", 1.10, ["5"]), ("1.50", "6,7", 1.50, ["6", "7"]),
                                    ("2.0", "8", 2.0, ["8"]), ("1.70", "10", 1.70, ["10"])]:
        cell = parse_cell(_cell_text(main, sup), set())
        assert cell.value == value and cell.footnotes == notes
        assert cell.text == main


def test_superscript_letters_and_full_size_digits():
    cell = parse_cell(_cell_text("1.25", "b"), {"b"})
    assert (cell.value, cell.footnotes, cell.text) == (1.25, ["b"], "1.25")
    chars = [_ch(c, 10 + 5 * i) for i, c in enumerate("1.105")]  # same size: a real number
    assert parse_cell(normalise(_split_size_runs("1.105", chars)), set()).value == 1.105


def _table(cols, rows=(), tid="Table 1", caption="Invented levels", footnotes=None):
    return Table("X", "", tid, caption, cols[:1], cols[1:], [TableRow({}, {c: Cell(r) for c in cols[1:]}) for r in rows],
                 footnotes or {})


def test_continuation_requires_same_header_on_next_page():
    base = _table(["No", "Test", "Levels"], ["a", "b"])
    same = _table(["No", "Test", "Levels"], ["c"], tid="")
    assert header_signature(base) == header_signature(_table(["No ", "TEST", "Levels"]))
    assert continues(base, 4, same, 5)
    assert not continues(base, 4, same, 6)  # a page in between
    assert not continues(base, 4, _table(["No", "Test", "Other"]), 5)
    assert not continues(None, None, same, 5)


def test_merge_continuation_chains_pages_and_keeps_row_pages():
    base = _table(["No", "Test", "Levels"], ["a"], footnotes={"a": "x"})
    merge_continuation(base, _table(["No", "Test", "Levels"], ["b"], footnotes={"a": "y", "b": "z"}), 5)
    merge_continuation(base, _table(["No", "Test", "Levels"], ["c"]), 6)
    assert [r.cells["Test"].text for r in base.rows] == ["a", "b", "c"]
    assert [r.page for r in base.rows] == [None, 5, 6]
    assert base.footnotes == {"a": "x", "b": "z"}
    assert "page" not in base.rows[0].to_dict() and base.rows[2].to_dict()["page"] == 6


def test_is_page_top():
    assert is_page_top(73, [30], 842)  # only the running header above
    assert not is_page_top(150, [30, 100], 842)  # body text above
    assert not is_page_top(300, [30], 842)  # too far down


def _line(text, top):
    return Line(text, 1, top, top + 10, 50, 10, 0, 0, "Body")


def test_trailing_caption_at_page_end():
    lines = [_line("Body text.", 100), _line("Table 1 Invented title", 700), _line("Page 3", 800)]
    cap = trailing_caption(lines, 842)
    assert cap and cap[1] == "Table 1 Invented title"
    assert trailing_caption([_line("Table 1 Invented title", 300), _line("More text.", 400)], 842) is None


def test_duplicate_ids_keep_first_unless_clearly_different():
    body = _table(["No", "Test"], ["a"], caption="Invented factors of safety")
    matrix = _table(["No", "Test"], ["b"], caption="Invented factors of safety")
    assert dedupe_tables([body, matrix]) == [body]
    assert dedupe_tables([body, _table(["No", "Test"], ["b"], caption="")]) == [body]
    other = _table(["No", "Test"], ["b"], caption="Completely unrelated compliance listing")
    assert dedupe_tables([body, other]) == [body, other]
