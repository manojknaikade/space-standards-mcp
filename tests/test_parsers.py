"""Unit tests for the ECSS / NASA / Word / table parsers on invented input (ADR-0002)."""

from spacestd.ecss_parser import parse_ecss_lines, word_lines
from spacestd.models import Table
from spacestd.nasa_parser import parse_nasa_lines
from spacestd.pdf_extract import (
    CAPTION_RE,
    Line,
    _CellText,
    _list_labels,
    _rotated_lines,
    _segment,
    _split_size_runs,
    normalise,
    parse_cell,
)
from spacestd.word_extract import accept_changes_xml


def L(text, *, page=1, top=0.0, x0=170.0, size=10.0, bold=0.0, italic=0.0, font="Body-Roman"):
    return Line(text=text, page=page, top=top, bottom=top + size, x0=x0, size=size, bold=bold, italic=italic, font=font)


def H(text, size=14.0, font="Head-Bold", **kw):
    return L(text, size=size, bold=1.0, font=font, **kw)


def lay(lines):
    """Give lines increasing positions so gaps look like one page of running text."""
    y = 80.0
    for ln in lines:
        ln.top, ln.bottom = y, y + ln.size
        y += ln.size + 3
    return lines


# --------------------------------------------------------------------------- ECSS


def demo_ecss():
    return lay([
        H("3 Terms"), L("a. A nomenclature item that is not a requirement shall be skipped."),
        H("9", size=22.0), H("Widgets", size=22.0),
        L("ECSS-E-ST-99_1234567", font="Mono-Bold", x0=400),
        L("a. The supplier shall paint every widget blue."),
        L("1. Primary widgets.", x0=198),
        L("2. Secondary widgets with a very long name that wraps onto", x0=198),
        L("the next line.", x0=227),
        L("NOTE 1 Blue is an invented colour rule.", x0=235),
        L("for testing only.", x0=284),
        L("NOTE 2 Second note.", x0=235),
        L("b. Widgets should be counted at least four", x0=170),
        L("(4) times.", x0=198),
        H("9.1 Deleted things", size=16.0),
        L("a. <<deleted>>"),
        L("b. Gadgets may be green."),
        H("9.1.1.1.1 Deep clause", size=11.0, font="Head-Roman"),
        L("a. Deep clauses shall work and refer to Table 9-1."),
        H("Annex A (informative)", size=12.0), H("Background", size=12.0),
        H("A.1 Context", size=13.0),
        L("a. Informative items are guidance."),
    ])


def test_ecss_two_captions_in_a_row_both_get_their_clause():
    # two tables on one page: with the table bodies out of the text flow, the second caption directly follows the
    # first and is not a wrapped line of it (32-11C Tables 5-3 / 5-4)
    lines = lay([
        H("9", size=22.0), H("Widgets", size=22.0),
        H("9.1 Criteria", size=16.0),
        L("a. Widgets shall meet Table 9-1 and Table 9-2."),
        H("Table 9-1: Invented widget criteria", size=12.0),
        H("Table 9-2: Invented gadget criteria", size=12.0),
        H("9.2 Later", size=16.0),
        L("a. Gadgets shall be counted."),
    ])
    reqs, info = parse_ecss_lines(lines, "ECSS-E-ST-99C", "Rev.1", table_lines={4: "Table 9-1", 5: "Table 9-2"})
    assert info["Table 9-1"][0] == info["Table 9-2"][0] == "9.1"
    assert [r.req_id for r in reqs] == ["9.1a", "9.2a"]


def test_ecss_ids_letters_notes_lists():
    lines = demo_ecss()
    lines[13].bold = 0.0  # 'Deep clause' heading style: not bold, other font, slightly larger
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-ST-99C", "Rev.1")
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["9a", "9b", "9.1a", "9.1b", "9.1.1.1.1a", "A.1a"]
    a = by["9a"]
    assert a.machine_id == "ECSS-E-ST-99_1234567"
    assert a.text.splitlines()[1:] == ["1. Primary widgets.", "2. Secondary widgets with a very long name that wraps onto the next line."]
    assert a.notes == ["Blue is an invented colour rule. for testing only.", "Second note."]
    assert a.heading_path == ["9 Widgets"]
    assert by["9b"].kind == "recommendation" and "four (4) times" in by["9b"].text
    assert by["9.1a"].kind == "deleted"
    assert by["9.1b"].kind == "permission"
    assert by["9.1.1.1.1a"].tables == ["Table 9-1"]
    assert by["A.1a"].kind == "guidance"


def test_word_lines_recompute_letters_and_flag_stale_refs():
    paragraphs = [
        "3 Terms", "    a. Skipped nomenclature.", "4 ", "Requirements", "4.1 General",
        "                        a. The supplier shall do one thing.",
        "    NOTE  An invented note.",
        "4.2 More",
        "                        b. The supplier shall do another thing.",  # Word runs letters on
        "                        c. As specified in 1.1.1b, it shall be checked.",
    ]
    reqs, _ = parse_ecss_lines(word_lines(paragraphs), "ECSS-E-ST-99C", "Rev.1", recompute_letters=True)
    assert [r.req_id for r in reqs] == ["4.1a", "4.2a", "4.2b"]
    assert reqs[0].notes == ["An invented note."]
    assert reqs[2].flags and "1.1.1b" in reqs[2].flags[0]


def test_ecss_level4_heading_without_number_h1():
    # H1 (docs/PARSING_NOTES.md): level-4 headings drawn in the heading font, number missing from the text layer
    head4 = dict(size=11.0, font="Head-Roman")
    lines = lay([
        H("5 Widgets", size=16.0),
        H("5.3 Control", size=13.0),
        H("5.3.5 Widget control words", size=12.0),
        L("a. The widget shall send a control word."),
        L("b. The widget shall echo it."),
        L("Start-of-widget word", **head4),
        L("a. The start word shall be first."),
        L("b. The start word shall be unique."),
        L("End-of-widget word with a title long enough", **head4),
        L("to wrap onto a second line", **head4),
        L("ECSS-E-ST-99_1234568", font="Mono-Bold", x0=400),
        L("a. The end word shall be last."),
        L("Figure label in the heading font", **head4),  # not followed by a restarting letter list
        L("b. The end word shall be even."),
        H("5.3.6 Spare words", size=12.0),
        L("5.3.6.1 Numbered spare", **head4),
        L("a. Spare words shall be zero."),
        L("Unnumbered spare", **head4),
        L("a. Unnumbered spares shall be zero too."),
        H("5.4 Status", size=13.0),
        L("5.4.1 Status word with a long numbered title that", **head4),
        L("wraps in the heading font", **head4),
        L("a. The status word shall be read."),
        H("Annex A (normative)", size=12.0),
        L("Unnumbered annex heading", **head4),  # no numbered annex clause yet: nothing to infer from
        L("a. Annex items shall stay under the annex."),
    ])
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-ST-99C", "Rev.1")
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["5.3.5a", "5.3.5b", "5.3.5.1a", "5.3.5.1b", "5.3.5.2a", "5.3.5.2b",
                        "5.3.6.1a", "5.3.6.2a", "5.4.1a", "Aa"]
    assert not any("duplicate" in r.req_id for r in reqs)
    assert by["5.3.5.1a"].heading_path == ["5 Widgets", "5.3 Control", "5.3.5 Widget control words",
                                          "5.3.5.1 Start-of-widget word"]
    assert by["5.3.5.2a"].heading_path[-1] == "5.3.5.2 End-of-widget word with a title long enough to wrap onto a second line"
    assert by["5.3.5.2a"].machine_id == "ECSS-E-ST-99_1234568"
    assert by["5.3.5.2b"].clause == "5.3.5.2" and "Figure label" not in by["5.3.5.2a"].text
    for rid in ("5.3.5.1a", "5.3.5.1b", "5.3.5.2a", "5.3.5.2b", "5.3.6.2a"):
        assert by[rid].flags == ["inferred clause number"]
    for rid in ("5.3.5a", "5.3.6.1a", "5.4.1a"):
        assert by[rid].flags == []
    assert by["5.4.1a"].heading_path[-1] == "5.4.1 Status word with a long numbered title that wraps in the heading font"



def test_ecss_prose_paragraphs_are_unparsed_h6():
    # H6 (docs/PARSING_NOTES.md): plain body paragraphs used to vanish without a trace
    lines = lay([
        H("3 Terms"), L("Nomenclature prose before the body is not counted."),
        H("4 Widget design guidance", size=16.0),
        H("4.1 General", size=13.0),
        L("Widgets are usually sized from the"),
        L("worst-case spin load, and margins are"),
        L("often reported per load case."),
        H("4.2 Margins", size=13.0),
        L("A margin table is commonly kept per"),
        L("widget assembly."),
        L("Spin axis", size=7.0, font="Fig-Roman"),  # figure label: dropped, not a paragraph
        L("A second paragraph after a gap."),
        L("a. The supplier shall record each margin."),
    ])
    lines[-2].top += 12  # paragraph gap before the second paragraph
    lines[-2].bottom += 12
    stats = {}
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-HB-99A", "", stats=stats)
    assert [r.req_id for r in reqs] == ["4.2a"]
    assert stats["unparsed"] == [
        "4.1: Widgets are usually sized from the worst-case spin load, and margins are often reported per load case.",
        "4.2: A margin table is commonly kept per widget assembly.",
        "4.2: A second paragraph after a gap.",
    ]
    assert stats["unparsed_words"] == 17 + 9 + 6
    # body = after the chapter-4 heading: headings, prose, the figure label and the requirement; not chapter 3
    assert stats["body_words"] == 2 + 17 + 2 + 9 + 2 + 6 + 7


def test_ecss_handbook_sections_become_guidance_records_a5():
    lines = lay([
        H("3 Terms"), L("Nomenclature prose before the body is not counted."),
        H("4 Widget design guidance", size=16.0),
        H("4.1 General", size=13.0),
        L("Widgets are usually sized from the"),
        L("worst-case spin load, and margins are"),
        L("often reported per load case."),
        L("A second paragraph after a gap."),
        L("NOTE Invented note on sizing."),
        H("4.2 Margins", size=13.0),
        L("A margin table is commonly kept."),
    ])
    lines[7].top += 12
    lines[7].bottom += 12
    stats = {}
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-HB-99A", "", handbook=True, stats=stats)
    assert [(r.req_id, r.kind, r.clause) for r in reqs] == [("4.1", "guidance", "4.1"), ("4.2", "guidance", "4.2")]
    assert reqs[0].text == ("Widgets are usually sized from the worst-case spin load, and margins are often reported per "
                            "load case.\nA second paragraph after a gap.")
    assert reqs[0].notes == ["Invented note on sizing."]
    assert reqs[0].heading_path == ["4 Widget design guidance", "4.1 General"]
    assert stats["unparsed"] == [] and stats["unparsed_words"] == 0


def test_word_handbook_paragraphs_join_one_record_a5():
    paragraphs = ["4 Widgets", "4.1 Sizing", "First invented paragraph.", "Second invented paragraph.", "4.2 Margins",
                  "Third invented paragraph."]
    stats = {}
    reqs, _ = parse_ecss_lines(word_lines(paragraphs), "ECSS-E-HB-99A", "", recompute_letters=True, handbook=True,
                               stats=stats)
    assert [(r.req_id, r.text) for r in reqs] == [
        ("4.1", "First invented paragraph.\nSecond invented paragraph."), ("4.2", "Third invented paragraph.")]
    assert stats["unparsed"] == []


def test_nasa_handbook_sections_become_guidance_records_a5():
    lines = lay([
        H("4. Handbook text", size=14.0, x0=72.0),
        H("4.1 Margins", size=12.0, x0=72.0),
        L("Invented prose about margins that the handbook explains at some length.", x0=72.0),
        L("A second invented paragraph about margins.", x0=72.0),
        H("4.2 Reports", size=12.0, x0=72.0),
        L("Invented prose about reports.", x0=72.0),
    ])
    lines[3].top += 12
    lines[3].bottom += 12
    reqs, unparsed = parse_nasa_lines(lines, "NASA-HDBK-9990", "", handbook=True)
    assert unparsed == []
    assert [(r.req_id, r.kind) for r in reqs] == [("4.1", "guidance"), ("4.2", "guidance")]
    assert reqs[0].text.count("\n") == 1
    # as a standard the same prose stays unparsed
    assert parse_nasa_lines(lines, "NASA-STD-9990", "")[1]


def test_ecss_demo_has_no_unparsed_text():
    stats = {}
    parse_ecss_lines(demo_ecss(), "ECSS-E-ST-99C", "Rev.1", stats=stats)
    assert stats["unparsed"] == [] and stats["unparsed_words"] == 0 and stats["body_words"] > 0


def test_word_paragraphs_are_separate_unparsed_fragments():
    paragraphs = ["4 Widgets", "First invented paragraph.", "Second invented paragraph.",
                  "a. Widgets shall be blue."]
    stats = {}
    reqs, _ = parse_ecss_lines(word_lines(paragraphs), "ECSS-E-ST-99C", "", recompute_letters=True, stats=stats)
    assert [r.req_id for r in reqs] == ["4a"]
    assert stats["unparsed"] == ["4: First invented paragraph.", "4: Second invented paragraph."]


def test_ecss_numbered_heading_at_body_size_h7():
    # H7: level-4 headings bold in the heading font but at body size (E-HB-32-24A layout, invented text)
    small = dict(size=10.0, font="Head-Bold")
    lines = lay([
        H("12 Widget joints chapter", size=16.0),
        H("12.6 Joints", size=14.0),
        H("12.6.4 Widget joints", size=12.0),
        H("12.6.4.1 Bolted widgets", **small),
        L("a. Bolt preload should be recorded."),
        L("b. Washers are usually hardened."),
        H("12.6.4.2 Bonded widgets with a title long", **small),
        H("enough to wrap", **small),
        L("a. Bond lines are often inspected."),
        H("12.6.4.7 Not the next number", **small),  # skips 3-6: not taken as a heading
        L("b. Bond lines should be dry."),
    ])
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-HB-99A", "")
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["12.6.4.1a", "12.6.4.1b", "12.6.4.2a", "12.6.4.2b"]
    assert by["12.6.4.1a"].heading_path == ["12 Widget joints chapter", "12.6 Joints", "12.6.4 Widget joints",
                                           "12.6.4.1 Bolted widgets"]
    assert by["12.6.4.2a"].heading_path[-1] == "12.6.4.2 Bonded widgets with a title long enough to wrap"
    assert all(r.flags == [] for r in reqs)


def test_accept_tracked_changes():
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    xml = f"""<w:document xmlns:w="{w}"><w:body>
      <w:p><w:r><w:t>Keep </w:t></w:r><w:del><w:r><w:delText>old </w:delText></w:r></w:del>
           <w:ins><w:r><w:t>new</w:t></w:r></w:ins></w:p>
      <w:p><w:pPr><w:rPr><w:del/></w:rPr></w:pPr><w:r><w:t>merged </w:t></w:r></w:p>
      <w:p><w:r><w:rPr><w:b/><w:rPrChange><w:rPr/></w:rPrChange></w:rPr><w:t>paragraph</w:t></w:r></w:p>
    </w:body></w:document>""".encode()
    out = accept_changes_xml(xml).decode()
    assert "old" not in out and "rPrChange" not in out and "<w:ins" not in out
    import re
    paras = re.findall(r"<w:p\b.*?</w:p>", out, re.S)
    texts = ["".join(re.findall(r"<w:t>(.*?)</w:t>", p)) for p in paras]
    assert texts == ["Keep new", "merged paragraph"]


# --------------------------------------------------------------------------- NASA


def demo_nasa():
    B = dict(bold=1.0, x0=72, size=12.0)
    T = dict(x0=72, size=12.0)
    I = dict(x0=72, size=12.0, italic=1.0)
    lines = [
        L("4. REQUIREMENTS", **B),
        L("4.1 Widgets", **B),
        L("Widgets are invented for this test.", **I),
        L("a. [XYZ 1] Each widget shall be inspected.", x0=108, size=12.0),
        L("b. [XYZ 2] Each widget shall be weighed, see [XYZ 1].", x0=108, size=12.0),
        L("[XYZ 3] Gadgets shall comply with all of the following:", **T),
        L("a. Be blue.", x0=108, size=12.0),
        L("b. Be light.", x0=108, size=12.0),
        L("A remark in italics between list items.", **I),
        L("c. Be quiet, as required by", x0=108, size=12.0),
        L("[XYZ 1].", **T),
        L("[Rationale: invented rationale.]", **I),
        L("4.2 Gadget details", **B),
        L("Gadgets are to comply with the items below to meet requirement [XYZ 3] section 4.1.", **T),
        L("a. Paint them.", x0=108, size=12.0),
        L("(1) With a brush.", x0=126, size=12.0),
        L("b. Dry them.", x0=108, size=12.0),
        L("APPENDIX A", **B),
        L("[XYZ 1] Matrix copy shall be ignored.", **T),
    ]
    y = 80.0
    for ln in lines:
        gap = 14 if ln.text[0].isupper() and not ln.text.startswith(("A remark",)) else 2
        ln.top, ln.bottom = y + gap, y + gap + ln.size
        y = ln.bottom
    return lines


def test_nasa_tags_items_guidance_and_body_only():
    reqs, unparsed = parse_nasa_lines(demo_nasa(), "NASA-STD-9999", "")
    by = {r.req_id: r for r in reqs}
    assert [r.req_id for r in reqs if r.kind == "requirement"] == [
        "XYZ 1", "XYZ 2", "XYZ 3", "XYZ 3 / 4.2", "XYZ 3 / 4.2.a", "XYZ 3 / 4.2.b"]
    assert by["XYZ 1"].clause == "4.1a"
    x3 = by["XYZ 3"].text
    assert "\na. Be blue." in x3 and "\nc. Be quiet, as required by [XYZ 1]." in x3  # list resumed after guidance
    assert by["XYZ 3"].notes == ["Rationale: invented rationale."]
    assert by["4.1 guidance 1"].kind == "guidance"
    assert by["XYZ 3 / 4.2.a"].parent == "XYZ 3" and "(1) With a brush." in by["XYZ 3 / 4.2.a"].text
    assert "Matrix copy" not in " ".join(r.text for r in reqs)
    assert unparsed == []


def test_nasa_third_level_items_and_list_after_guidance():
    """'A.'/'ii.' under '(n)' stay in the lettered item; '(n)' after guidance returns to its owner."""
    T = dict(x0=72, size=12.0)
    lines = [
        L("4. REQUIREMENTS", bold=1.0, x0=72, size=12.0),
        L("4.1 Gizmos", bold=1.0, x0=72, size=12.0),
        L("[QRS 1] Gizmos shall satisfy section 4.2.", **T),
        L("4.2 Gizmo details", bold=1.0, x0=72, size=12.0),
        L("Satisfy the following to meet requirement [QRS 1] section 4.1.", **T),
        L("a. Assess them as follows:", x0=108, size=12.0),
        L("(1) Pick one of the following:", x0=126, size=12.0),
        L("A. Option one.", x0=144, size=12.0),
        L("B. Option two with a factor of 9.9.", x0=144, size=12.0),
        L("i. First detail. ii. Second detail.", x0=162, size=12.0),
        L("An invented italic remark inside the list.", x0=72, size=12.0, italic=1.0),
        L("(2) Another item after the remark.", x0=126, size=12.0),
        L("b. Report them.", x0=108, size=12.0),
        L("APPENDIX A", bold=1.0, x0=72, size=12.0),
    ]
    y = 80.0
    for ln in lines:
        ln.top, ln.bottom = y + 14, y + 14 + ln.size
        y = ln.bottom
    reqs, unparsed = parse_nasa_lines(lines, "NASA-STD-9998", "")
    by = {r.req_id: r for r in reqs}
    a = by["QRS 1 / 4.2.a"].text
    assert a.splitlines() == ["Assess them as follows:", "(1) Pick one of the following:", "A. Option one.",
                              "B. Option two with a factor of 9.9.", "i. First detail. ii. Second detail.",
                              "(2) Another item after the remark."]
    assert by["QRS 1 / 4.2"].text == "Satisfy the following to meet requirement [QRS 1] section 4.1."
    assert by["4.2 guidance 1"].text == "An invented italic remark inside the list."
    assert by["QRS 1 / 4.2.b"].text == "Report them."
    assert unparsed == []


def _tagless_lines(extra=()):
    """Invented reproduction of PARSING_NOTES H2: no bracketed tags in the body."""
    B = dict(bold=1.0, x0=72, size=12.0)
    T = dict(x0=72, size=12.0)
    lines = [
        L("4. REQUIREMENTS", **B),
        L("4.1 Scope of widgets", **B),
        L("This section describes widgets in general.", **T),
        L("4.2 Widget handling", **B),
        L("a. The operator shall ground the widget before", x0=90, size=12.0),
        L("handling.", x0=90, size=12.0),
        L("b. Widgets shall be stored in a dry container.", x0=90, size=12.0),
        L("c. A note that is not a requirement.", x0=90, size=12.0),
        L("4.3 Gizmo checks", **B),
        L("1. Each gizmo shall be inspected before use.", x0=90, size=12.0),
        L("(1) The inspection shall be logged.", x0=108, size=12.0),
        L("2. Each gizmo shall be cleaned.", x0=90, size=12.0),
        L("4.4 Gadget logs", **B),
        L("The supplier shall keep a gadget log with the following:", **T),
        L("a. The gadget number.", x0=90, size=12.0),
        L("b. The date of use.", x0=90, size=12.0),
        L("Each gadget shall be weighed once a year.", **T),
        *extra,
        L("APPENDIX A", **B),
        L("a. Matrix copy shall be ignored.", **T),
    ]
    y = 80.0
    for ln in lines:
        gap = 2 if ln.text == "handling." else 14
        ln.top, ln.bottom = y + gap, y + gap + ln.size
        y = ln.bottom
    return lines


def test_nasa_tagless_items_become_requirements():
    reqs, unparsed = parse_nasa_lines(_tagless_lines(), "NASA-STD-9997", "")
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["4.2a", "4.2b", "4.3(1)", "4.3(2)", "4.4 req 1", "4.4 req 2"]
    assert by["4.2a"].text == "The operator shall ground the widget before handling."
    assert by["4.2a"].clause == "4.2" and by["4.2a"].heading_path == ["4 REQUIREMENTS", "4.2 Widget handling"]
    assert by["4.3(1)"].text == "Each gizmo shall be inspected before use.\n(1) The inspection shall be logged."
    assert by["4.4 req 1"].text.splitlines() == ["The supplier shall keep a gadget log with the following:",
                                                 "a. The gadget number.", "b. The date of use."]
    assert all(r.kind == "requirement" for r in reqs)
    assert "Matrix copy" not in " ".join(r.text for r in reqs)
    # no 'shall': stays unparsed, as before
    assert unparsed == ["4.1: This section describes widgets in general.", "4.2: c. A note that is not a requirement."]


def test_nasa_body_without_section_4_heading_h6():
    """H6: no bold '4 Title' heading used to return nothing at all."""
    B = dict(bold=1.0, x0=72, size=12.0)
    T = dict(x0=72, size=12.0)

    def place(lines):
        y = 80.0
        for ln in lines:
            ln.top, ln.bottom = y + 14, y + 14 + ln.size
            y = ln.bottom
        return lines

    # '4.0 Title' is a section-4 heading
    lines = place([L("1.0 SCOPE", **B), L("The scope shall be ignored.", **T),
                   L("4.0 GENERAL", **B), L("4.1 Widgets", **B), L("Each widget shall be blue.", **T)])
    stats = {}
    reqs, unparsed = parse_nasa_lines(lines, "NASA-HDBK-9993", "", stats=stats)
    assert [r.req_id for r in reqs] == ["4.1 req 1"] and unparsed == []
    assert stats == {"unparsed_words": 0, "body_words": 2 + 2 + 5}
    # no section 4 at all: the body starts at the first numbered heading
    lines = place([L("Cover text of an invented handbook.", **T), L("2 WIDGET PRACTICE", **B),
                   L("Widgets are usually painted.", **T), L("2.1 Gadgets", **B), L("Gadgets shall be green.", **T)])
    reqs, unparsed = parse_nasa_lines(lines, "NASA-HDBK-9992", "", stats=stats)
    assert [r.req_id for r in reqs] == ["2.1 req 1"]
    assert unparsed == ["2: Widgets are usually painted."] and stats["unparsed_words"] == 4
    # no numbered heading either: every paragraph comes back unparsed instead of vanishing
    lines = place([L("Invented text without headings.", **T), L("More invented text.", **T)])
    reqs, unparsed = parse_nasa_lines(lines, "NASA-HDBK-9991", "", stats=stats)
    assert reqs == [] and unparsed == [": Invented text without headings.", ": More invented text."]
    assert stats == {"unparsed_words": 7, "body_words": 7}


def test_nasa_tagged_document_is_not_tagless():
    """One tag definition in the body keeps the tagged rules: untagged items are not made requirements."""
    lines = _tagless_lines(extra=[L("4.5 Gadget limits", bold=1.0, x0=72, size=12.0),
                                  L("[XYZ 7] Each gadget shall be tested.", x0=72, size=12.0)])
    reqs, unparsed = parse_nasa_lines(lines, "NASA-STD-9996", "")
    assert [r.req_id for r in reqs] == ["XYZ 7"]
    assert any(u.startswith("4.2: a. The operator") for u in unparsed)


def test_nasa_tag_prefix_with_digit():
    """'[V7 1234]' (prefix ending in a digit, like NASA-STD-3001 Vol 2) is a tag."""
    T = dict(x0=72, size=12.0)
    lines = [
        L("4. REQUIREMENTS", bold=1.0, x0=72, size=12.0),
        L("4.4 Gadget logs [V7 1234] Each gadget shall have a log.", **T),
        L("4.5 Gadget storage", bold=1.0, x0=72, size=12.0),
        L("[V7 1235] Gadgets shall be stored dry, see [V7 1234].", **T),
        L("APPENDIX A", bold=1.0, x0=72, size=12.0),
    ]
    y = 80.0
    for ln in lines:
        ln.top, ln.bottom = y + 14, y + 14 + ln.size
        y = ln.bottom
    reqs, unparsed = parse_nasa_lines(lines, "NASA-STD-9995", "")
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["V7 1234", "V7 1235"]
    assert by["V7 1234"].clause == "4.4" and by["V7 1234"].text == "Each gadget shall have a log."
    assert unparsed == []


def test_nasa_subscript_fragment_lines_do_not_break_a_list():
    """A subscript on a line of its own ('K' + 't', 'K' + 'm'; 5017B DDMR 46) is neither a paragraph nor the
    line a list item follows: the tagged requirement keeps all its items."""
    B = dict(bold=1.0, x0=72, size=12.0)
    T = dict(x0=72, size=12.0)
    I = dict(x0=108, size=12.0)
    S = dict(x0=190, size=8.0, italic=1.0)
    lines = [
        (L("4. REQUIREMENTS", **B), 0), (L("4.5 Gizmo motors", **B), 30),
        (L("4.5.1. [GMR 3] Each gizmo motor shall have the following measured:", **T), 60),
        (L("a. Spin constant (K).", **I), 88), (L("s", **S), 96),
        (L("b. Hum constant (K ).", **I), 102), (L("h", **S), 110),
        (L("c. Spin versus load curve.", **I), 116),
        (L("d. Coil resistance.", **I), 130),
        (L("4.5.2. [GMR 4] Each gizmo shall be weighed.", **T), 158),
        (L("APPENDIX A", **B), 190),
    ]
    for ln, top in lines:
        ln.top, ln.bottom = top + 80, top + 80 + ln.size
    reqs, _ = parse_nasa_lines([ln for ln, _ in lines], "NASA-STD-9993", "")
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["GMR 3", "GMR 4"]
    assert [x[:2] for x in by["GMR 3"].text.split("\n")[1:]] == ["a.", "b.", "c.", "d."]


def test_nasa_lead_tag_after_dotted_paragraph_number():
    """Invented reproduction of PARSING_NOTES H5: '4.3.1.1. [WTR 5] ...' (trailing dot) is a tag definition."""
    B = dict(bold=1.0, x0=72, size=12.0)
    T = dict(x0=72, size=12.0)
    lines = [
        L("4. REQUIREMENTS", **B),
        L("4.3 Widget tests", **B),
        L("4.3.1 Shaking", **B),
        L("4.3.1.1. [WTR 5] Each widget shall be shaken before delivery.", **T),
        L("4.3.1.2. [WTR 6] The shaking level shall be logged.", **T),
        L("4.3.2 Spinning", **B),
        L("4.3.2.1. [WTR 7] Spin tests shall use a balanced fixture.", **T),
        L("APPENDIX A", **B),
    ]
    y = 80.0
    for ln in lines:
        ln.top, ln.bottom = y + 14, y + 14 + ln.size
        y = ln.bottom
    reqs, unparsed = parse_nasa_lines(lines, "NASA-STD-9994", "")
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["WTR 5", "WTR 6", "WTR 7"]  # not tagless: no '4.3.1 req N' IDs
    assert by["WTR 5"].text == "Each widget shall be shaken before delivery."
    assert by["WTR 5"].clause == "4.3.1.1" and by["WTR 7"].clause == "4.3.2.1"
    assert by["WTR 6"].heading_path[:3] == ["4 REQUIREMENTS", "4.3 Widget tests", "4.3.1 Shaking"]
    assert by["WTR 7"].heading_path[2] == "4.3.2 Spinning"
    assert unparsed == []


# --------------------------------------------------------------------------- tables


def test_parse_cell_values_and_footnotes():
    keys = {"a", "b", "c", "e", "*", "**"}
    assert parse_cell("1,25 a, e", keys).to_dict() == {"text": "1,25 a, e", "value": 1.25, "footnotes": ["a", "e"]}
    assert parse_cell("1.0*", keys).value == 1.0 and parse_cell("1.0*", keys).footnotes == ["*"]
    c = parse_cell("N/A or 1.05**", keys)
    assert c.value is None and c.footnotes == ["**"]
    assert parse_cell("See Note c", keys).footnotes == ["c"]
    assert parse_cell("1 or Jp c", keys).value is None


def test_segment_stacked_and_merged_cells():
    anchors = [100.0, 120.0]
    stacked = _CellText((0, 90, 50, 130), [("9,9", 100.0, False), ("8,8", 120.0, False)])
    assert _segment(stacked, anchors, is_value=True) == {100.0: "9,9", 120.0: "8,8"}
    merged = _CellText((0, 90, 50, 130), [("See Note z", 100.0, False)])
    assert _segment(merged, anchors, is_value=True) is None  # one value in a merged cell spans both rows
    label = _CellText((0, 85, 50, 130), [("Group", 90.0, False), ("- Left", 100.0, False), ("- Right", 120.0, False)])
    assert _segment(label, anchors, is_value=False) == {100.0: "Group - Left", 120.0: "Group - Right"}
    wrapped = _CellText((0, 90, 50, 170), [("Long label", 100.0, False), ("wraps", 120.0, False)])
    assert _segment(wrapped, anchors + [140.0, 160.0], is_value=False) is None


def test_normalise_hyphens():
    assert normalise("ECSS‐E‐ST‐32C  Rev.1") == "ECSS-E-ST-32C Rev.1"


def test_table_citation():
    t = Table("DEMO-1", "Rev.1", "Table 9-1", "Invented", ["Vehicle"], ["F"], [])
    assert t.citation == "DEMO-1 Rev.1, Table 9-1"


def test_caption_without_separator():
    assert CAPTION_RE.match("Table 5-1 Invented couples").groups() == ("5-1", "Invented couples")
    assert CAPTION_RE.match("Table 4-2: Invented factors").groups() == ("4-2", "Invented factors")
    assert CAPTION_RE.match("Table 3—Invented").groups() == ("3", "Invented")
    assert CAPTION_RE.match("Table 1―Invented title").groups() == ("1", "Invented title")  # U+2015 bar
    assert CAPTION_RE.match("Table 2‒Invented title").groups() == ("2", "Invented title")  # U+2012
    assert CAPTION_RE.match("Table 5-1 of the other standard") is None  # a reference, not a caption


def _ch(text, x0, top, size=10.0, upright=True):
    return {"text": text, "x0": x0, "x1": x0 + 0.6 * size, "top": top, "bottom": top + size, "size": size,
            "fontname": "Body-Roman", "upright": upright}


def test_split_size_runs_spaces_word_subscripts_only():
    chars = [_ch(c, 10 + 5 * i, 0) for i, c in enumerate("9,9")] + [_ch(c, 30 + 3 * i, 3, 6.0) for i, c in enumerate("fixed")]
    assert _split_size_runs("9,9fixed", chars) == "9,9 fixed"
    chars = [_ch("K", 10, 0), _ch("q", 16, 3, 6.0), _ch(" ", 20, 0), _ch("z", 24, 0, 6.0)]
    assert _split_size_runs("Kq z", chars) == "Kq z"  # one-letter subscript and spaced marker unchanged


def test_rotated_header_reads_bottom_to_top():
    word = "Zinc"  # rotated 90°: letters stacked upwards, first letter lowest
    chars = [_ch(c, 50, 100 - 10 * i, upright=False) for i, c in enumerate(word)]
    chars += [_ch(c, 62, 100 - 10 * i, upright=False) for i, c in enumerate("Tin")]
    assert [t for t, _, _ in _rotated_lines(chars, 80.0)] == ["Zinc", "Tin"]


def test_list_label_repeats_per_band():
    anchors = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
    group = _CellText((0, 5, 50, 65), [("Joints:", 25.0, False), ("- One", 30.0, False), ("- Two", 35.0, False),
                                       ("(more)", 40.0, False), ("- Three", 45.0, False)])
    bands = [_CellText((50, 5, 90, 35), [("Band A", 20.0, False)]), _CellText((50, 35, 90, 65), [("Band B", 50.0, False)])]
    got = _list_labels(group, anchors, bands)
    assert [got[a] for a in anchors] == ["Joints: - One", "Joints: - Two (more)", "Joints: - Three"] * 2
    assert _list_labels(group, anchors, bands[:1]) is None  # bands must account for every row


def test_ecss_handbook_section_resumes_after_an_interruption_a5():
    """Real handbooks resume a section's prose after a list or table; it joins the section's record (no
    `(duplicate n)` IDs: E-HB-32-25A had 416)."""
    from spacestd.ecss_parser import _Builder

    b = _Builder("ECSS-E-HB-99A", "", False, handbook=True)
    b.clause = "4.1"
    b.start_section("First invented paragraph.", 1)
    b.finish()  # e.g. a table or a list item closed the record
    b.start_section("Invented prose after the table.", 2)
    b.finish()
    assert [(r.req_id, r.text) for r in b.reqs] == [("4.1", "First invented paragraph.\nInvented prose after the table.")]


# --------------------------------------------------------------------------- B3 fixes (H13, H14, H8)


def test_ecss_unnumbered_level4_sized_by_font_h13a():
    # H13a: unnumbered 12 pt bold headings take the next free level-4 number, with or without a list
    l4 = dict(size=12.0, font="Head-Bold")
    lines = lay([
        H("9 Chapter", size=22.0),
        H("9.1 X", size=16.0),
        H("9.1.1 Y", size=14.0),
        H("General", **l4),  # prose only: still takes 9.1.1.1
        L("Some descriptive prose follows the heading."),
        L("NOTE Invented note."),
        H("Alpha", **l4),
        L("a. Alpha items shall be listed."),
        L("b. Alpha items shall be sorted."),
        H("9.1.1.2.1 Deep numbered heading", size=10.0),  # level 5 at body size (H7)
        L("c. Deep items shall be kept."),
        H("Beta", **l4),  # after a numbered level-5 heading: sibling of Alpha, not its child
        L("a. Beta items shall be listed."),
    ])
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-ST-99C", "Rev.1")
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["9.1.1.2a", "9.1.1.2b", "9.1.1.2.1c", "9.1.1.3a"]
    assert by["9.1.1.2a"].flags == ["inferred clause number"]
    assert by["9.1.1.3a"].heading_path == ["9 Chapter", "9.1 X", "9.1.1 Y", "9.1.1.3 Beta"]


def test_ecss_drd_heading_at_body_size_h13b():
    # H13b: a bold '<n>' item heading set at body size was read as text of the previous item
    lines = lay([
        H("4 Chapter", size=16.0),
        H("A.1 DRD", size=14.0),
        H("<8> Eighth item", size=11.0),
        L("a. The eighth item shall be present."),
        H("<9> Ninth item", size=10.0, font="Body-Bold"),
        L("a. The ninth item shall be present."),
    ])
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-ST-99C", "Rev.1")
    assert [r.req_id for r in reqs] == ["A.1<8>a", "A.1<9>a"]


def test_ecss_equation_numbers_are_not_headings_h14():
    eq = dict(size=12.0, font="Serif-Roman", x0=421.0)
    lines = lay([
        H("5 Chapter", size=16.0),
        H("5.5 Widgets", size=14.0),
        L("f. The widget model shall include:", x0=170.0),
        L("1. the first term;", x0=199.0),
        L("2. the second term,", x0=199.0),
        L("1 1", **eq),
        L("2 2", **eq),
        L("3. the third term;", x0=199.0),
        L("4. the fourth term.", x0=199.0),
        L("g. The widget shall be checked.", x0=170.0),
    ])
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-ST-99C", "Rev.1")
    assert [r.req_id for r in reqs] == ["5.5f", "5.5g"]
    assert "4. the fourth term." in reqs[0].text and "the first term" in reqs[0].text


def test_ecss_deleted_typo_and_can_kinds_h14():
    lines = lay([
        H("5 Chapter", size=16.0),
        H("5.1 Widgets", size=14.0),
        L("a. The widget shall exist."),
        L("b. >>deleted>>"),
        L("c. The widget can be rotated."),
        L("d. The widget cannot be opened and can be closed."),
        L("e. The widget can be rotated and shall be locked."),
    ])
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-ST-99C", "Rev.1")
    assert [r.kind for r in reqs] == ["requirement", "deleted", "guidance", "guidance", "requirement"]


def test_ecss_glossary_handbook_h8():
    # E-HB-32-20 Part 8A layout: upper-case term at the margin, definition indented below it
    gl = dict(size=16.0, font="Head2-Bold")
    d = dict(x0=85.0)
    lines = lay([
        L("Front matter text that is not in the body."),
        H("1 Glossary", size=22.0),
        H("A", **gl),
        L("ALPHA-FIBRE", x0=71.0),
        L("A thread made of invented material", **d),
        L("and spun twice.", **d),
        L("NOTE Invented note on the fibre.", **d),
        L("AXIS", x0=71.0),
        L("1 A line about which things turn.", **d),
        L("2 A reference line.", **d),
        H("B", **gl),
        L("BOLT (THREADED)", x0=71.0),
        L("A fastener: used in joints.", **d),
        H("2 References", size=22.0),
        L("[1] Invented reference."),
    ])
    stats = {}
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-HB-99A", "", handbook=True, stats=stats)
    assert [(r.req_id, r.kind) for r in reqs] == [
        ("1:ALPHA-FIBRE", "guidance"), ("1:AXIS", "guidance"), ("1:BOLT (THREADED)", "guidance"), ("2", "guidance")]
    assert reqs[0].flags == ["glossary term"] and reqs[0].clause == "1"
    assert reqs[0].text.startswith("A thread made of invented material and spun twice.")
    assert "Invented note" in reqs[0].text and "A reference line." in reqs[1].text
    assert stats["body_words"] > 0
    from spacestd.health import GLOSSARY_ID_RE, SECTION_ID_RE
    assert all(GLOSSARY_ID_RE.match(r.req_id) for r in reqs[:3]) and SECTION_ID_RE.match("2")


def _spread(lines, gap=14):
    """Every line its own paragraph: a fixed vertical gap between lines (single page)."""
    y = 80.0
    for ln in lines:
        ln.top, ln.bottom = y + gap, y + gap + ln.size
        y = ln.bottom
    return lines


_NB = dict(bold=1.0, x0=72, size=12.0)
_NT = dict(x0=72, size=12.0)


def test_nasa_tagged_non_requirement_paragraphs_are_not_records_h12():
    lines = _spread([
        L("4. REQUIREMENTS", **_NB),
        L("4.1 Widgets", **_NB),
        L("[WDG 1] Each widget shall be inspected.", **_NT),
        L("E = m c squared (invented equation)", **_NT),
        L("The invented legend may be read as a key.", **_NT),  # descriptive 'may': no statement
        L("Widgets shall also be weighed.", **_NT),
        L("4.2 Gadgets", **_NB),
        L("[WDG 2] Gadgets shall meet all of the following:", **_NT),
        L("a. Be blue.", x0=90, size=12.0),
        L("b. Be light.", x0=90, size=12.0),
        L("Mounting bracket, pitch 4 mm", **_NT),
        L("4.3 Retired", **_NB),
        L("[WDG 7] Deleted Requirement", **_NT),
        L("APPENDIX A", **_NB),
    ])
    reqs, unparsed = parse_nasa_lines(lines, "NASA-STD-9980", "")
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["WDG 1", "WDG 1 / 4.1", "WDG 2", "WDG 7"]  # no false record for the equation
    assert by["WDG 1 / 4.1"].text == "Widgets shall also be weighed."
    assert by["WDG 2"].text.splitlines() == ["Gadgets shall meet all of the following:", "a. Be blue.", "b. Be light.",
                                             "Mounting bracket, pitch 4 mm"]
    assert by["WDG 7"].kind == "deleted" and by["WDG 7"].clause == "4.3"
    assert unparsed == ["4.1: E = m c squared (invented equation)", "4.1: The invented legend may be read as a key."]


def test_nasa_tagless_numbered_paragraphs_get_their_own_ids_h9():
    lines = _spread([
        L("4. REQUIREMENTS", **_NB),
        L("4.3 Widget tests", **_NB),
        L("4.3.1 The widget shall be shaken.", **_NT),
        L("4.3.1.1 The shaking level shall be logged.", **_NT),
        L("4.3.2 The widget should be spun.", **_NT),
        L("4.3.3 Each gizmo shall be cleaned and", **_NT),
        L("dried.", **_NT),
        L("APPENDIX A", **_NB),
    ])
    lines[6].top -= 12  # 'dried.' continues the paragraph
    lines[6].bottom -= 12
    reqs, unparsed = parse_nasa_lines(lines, "NASA-STD-9979", "")
    assert [(r.req_id, r.text) for r in reqs] == [
        ("4.3.1", "The widget shall be shaken."),
        ("4.3.1.1", "The shaking level shall be logged."),
        ("4.3.3", "Each gizmo shall be cleaned and dried.")]
    assert unparsed == ["4.3: 4.3.2 The widget should be spun."]


def test_nasa_tagless_upright_lead_in_that_points_at_a_table_is_guidance():
    # 7003A 4.3: an upright paragraph without 'shall' under a heading, pointing at a table. Other prose
    # without 'shall' (no table) stays unparsed; italic guidance keeps its numbering after the lead-in.
    lines = _spread([
        L("4. REQUIREMENTS", **_NB),
        L("4.3 Widget tests", **_NB),
        L("Widgets can rattle in odd ways. Typical limits are listed in table 1 of section 1.6.", **_NT),
        L("4.3.1 The widget shall be rattled.", **_NT),
        L("An invented italic remark about widgets.", x0=72, size=12.0, italic=1.0),
        L("4.4 Gadget tests", **_NB),
        L("Gadgets are discussed with no table at all.", **_NT),
        L("4.4.1 The gadget shall be spun.", **_NT),
        L("APPENDIX A", **_NB),
    ])
    reqs, unparsed = parse_nasa_lines(lines, "NASA-STD-9979", "")
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["4.3 guidance 1", "4.3.1", "4.3 guidance 2", "4.4.1"]
    lead = by["4.3 guidance 1"]
    assert lead.kind == "guidance" and lead.tables == ["Table 1"]
    assert unparsed == ["4.4: Gadgets are discussed with no table at all."]


def test_nasa_italic_tail_on_the_line_does_not_split_a_numbered_paragraph():
    # the requirement wraps onto a line whose rest is italic guidance: still one paragraph (7003A 4.1.1)
    lines = _spread([
        L("4. REQUIREMENTS", **_NB),
        L("4.3 Widget tests", **_NB),
        L("An invented italic remark about widgets.", x0=72, size=12.0, italic=1.0),
        L("4.3.1 If a widget may rattle on the bench, then a rattle", **_NT),
        L("test shall be performed. An early rattle check is a good idea.", x0=72, size=12.0, italic=0.7),
        L("It saves widgets from a late surprise in the program and spares", x0=72, size=12.0, italic=1.0),
        L("the bench a lot of noise during the later widget campaigns.", x0=72, size=12.0, italic=1.0),
        L("4.3.2 The widget shall be spun.", **_NT),
        L("APPENDIX A", **_NB),
    ])
    for k, ln in enumerate(lines[4:7], 1):  # the wrapped lines continue the paragraph
        ln.top -= 12 * k
        ln.bottom -= 12 * k
    reqs, _ = parse_nasa_lines(lines, "NASA-STD-9979", "")
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["4.3 guidance 1", "4.3.1", "4.3.2"]
    assert by["4.3.1"].text.startswith("If a widget may rattle") and "test shall be performed" in by["4.3.1"].text


def test_nasa_italic_headings_in_tagless_body_h13c():
    it = dict(x0=72, size=12.0, italic=1.0)
    lines = _spread([
        L("4. REQUIREMENTS", **_NB),
        L("4.1 Widgets", **_NB),
        L("4.1.1 Sub-widgets", **it),
        L("Each widget shall be inspected.", **_NT),
        L("4.1.2 More sub-widgets", **it),
        L("Each gizmo shall be cleaned.", **_NT),
        L("7.9 Stray number that is not a next heading", **it),
        L("Each gadget shall be weighed.", **_NT),
        L("4.1.3 This italic sentence shall not be a heading at all.", **it),
        L("APPENDIX A", **_NB),
    ])
    reqs, _ = parse_nasa_lines(lines, "NASA-STD-9978", "")
    assert [(r.req_id, r.clause, r.heading_path[-1]) for r in reqs if r.kind == "requirement"] == [
        ("4.1.1 req 1", "4.1.1", "4.1.1 Sub-widgets"), ("4.1.2 req 1", "4.1.2", "4.1.2 More sub-widgets"),
        ("4.1.2 req 2", "4.1.2", "4.1.2 More sub-widgets")]


def test_nasa_bold_heading_with_trademark_glyph_h13c():
    lines = _spread([
        L("4. REQUIREMENTS", **_NB),
        L("4.7.2 Widgets", **_NB),
        L("Each widget shall be inspected.", **_NT),
        L("4.7.3 Gizmos®", bold=0.7, x0=72, size=12.0),
        L("Each gizmo shall be cleaned.", **_NT),
        L("APPENDIX A", **_NB),
    ])
    reqs, _ = parse_nasa_lines(lines, "NASA-STD-9977", "")
    assert [r.req_id for r in reqs] == ["4.7.2 req 1", "4.7.3 req 1"]


def test_nasa_tag_inside_list_item_or_guidance_block_starts_a_record_h14():
    lines = _spread([
        L("4. REQUIREMENTS", **_NB),
        L("4.1 Widgets", **_NB),
        L("[WDG 178] Each widget shall be one of the following:", **_NT),
        L("A. [WDG 180] A widget shall be blue.", x0=90, size=12.0),
        L("B. [WDG 181] A widget shall be light.", x0=90, size=12.0),
        L("An invented italic note about colours.", x0=72, size=12.0, italic=1.0),
        L("[WDG 182] A widget shall be quiet.", x0=72, size=12.0, italic=1.0),
        L("APPENDIX A", **_NB),
    ])
    reqs, _ = parse_nasa_lines(lines, "NASA-STD-9976", "")
    by = {r.req_id: r for r in reqs}
    assert [r.req_id for r in reqs if r.kind == "requirement"] == ["WDG 178", "WDG 180", "WDG 181", "WDG 182"]
    assert by["WDG 178"].text == "Each widget shall be one of the following:"
    assert by["WDG 180"].text == "A widget shall be blue."
    assert by["4.1 guidance 1"].text == "An invented italic note about colours."


def test_nasa_figure_caption_closes_its_paragraph_h14():
    lines = [
        L("4. REQUIREMENTS", page=1, top=80.0, **_NB),
        L("4.1 Widgets", page=1, top=100.0, **_NB),
        L("[WDG 100] Widgets shall be listed:", page=1, top=120.0, **_NT),
        L("d. [WDG 102] A widget shall be round.", page=1, top=140.0, x0=90, size=12.0),
        L("Figure 4—Invented widget", page=2, top=700.0, **_NB),
        L("e. [WDG 103] A widget shall be flat.", page=3, top=80.0, x0=90, size=12.0),
        L("APPENDIX A", page=3, top=300.0, **_NB),
    ]
    for ln in lines:
        ln.bottom = ln.top + ln.size
    reqs, _ = parse_nasa_lines(lines, "NASA-STD-9975", "")
    assert [r.req_id for r in reqs] == ["WDG 100", "WDG 102", "WDG 103"]


def test_nasa_handbook_uppercase_plain_headings_h8():
    lines = _spread([
        L("1. INTRODUCTION ........ 1", **_NT),
        L("1.1 PURPOSE ........ 1", **_NT),
        L("2. DEFINITIONS 4", **_NT),
        L("1. INTRODUCTION", **_NT),
        L("Invented prose of the introduction.", **_NT),
        L("1.1 PURPOSE:", **_NT),
        L("Invented prose of the purpose.", **_NT),
        L("2. DEFINITIONS", **_NT),
        L("Invented definitions prose.", **_NT),
    ])
    reqs, unparsed = parse_nasa_lines(lines, "NASA-HDBK-9974", "", handbook=True)
    assert [(r.req_id, r.kind, r.text) for r in reqs] == [
        ("1", "guidance", "Invented prose of the introduction."),
        ("1.1", "guidance", "Invented prose of the purpose."),
        ("2", "guidance", "Invented definitions prose.")]
    assert unparsed == []


def test_ecss_level3_size_is_the_commonest_h13a():
    # one odd 11 pt level-3 heading must not hide the 12 pt unnumbered level-4 headings (10-03C)
    lines = lay([
        H("3 Terms", size=22.0),
        H("3.2 Defined terms", size=16.0),
        H("3.2.1 widget", size=11.0),  # terms set as 11 pt level-3 headings, more of them than body ones
        H("3.2.2 gadget", size=11.0),
        H("3.2.3 gizmo", size=11.0),
        H("9 Chapter", size=22.0),
        H("9.1 X", size=16.0),
        H("9.1.1 Y", size=14.0),
        L("a. Y items shall be listed."),
        H("9.1.2 Odd", size=11.0),
        L("a. Odd items shall be listed."),
        H("9.1.3 W", size=14.0),
        H("General", size=12.0),
        L("Some descriptive prose follows the heading."),
        H("Alpha", size=12.0),
        L("a. Alpha items shall be listed."),
    ])
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-ST-99C", "Rev.1")
    assert [r.req_id for r in reqs] == ["9.1.1a", "9.1.2a", "9.1.3.2a"]


def test_ecss_drd_heading_with_plain_brackets_h13b():
    # '<9>' in the body font, bold except the angle brackets (bold share 0.79 < 0.8)
    lines = lay([
        H("4 Chapter", size=16.0),
        H("A.1 DRD", size=14.0),
        L("<8> Eighth item", size=12.0, bold=0.84, font="Body-Bold"),
        L("a. The eighth item shall be present."),
        L("<9> Ninth item", size=12.0, bold=0.79, font="Body-Bold"),
        L("a. The ninth item shall be present."),
    ])
    reqs, _ = parse_ecss_lines(lines, "ECSS-E-ST-99C", "Rev.1")
    assert [r.req_id for r in reqs] == ["A.1<8>a", "A.1<9>a"]


def test_nasa_heading_number_split_from_its_title_h13c():
    lines = _spread([
        L("4. REQUIREMENTS", **_NB),
        L("4.7.2 Widgets", **_NB),
        L("Each widget shall be inspected.", **_NT),
        L("4.7.3", **_NB),
        L("Gizmos®", bold=1.0, x0=108, size=12.0),
        L("Each gizmo shall be cleaned.", **_NT),
        L("APPENDIX A", **_NB),
    ])
    lines[4].top, lines[4].bottom = lines[3].top + 3, lines[3].bottom + 3  # title baseline a few points lower
    reqs, _ = parse_nasa_lines(lines, "NASA-STD-9980", "")
    assert [r.clause for r in reqs] == ["4.7.2", "4.7.3"]
    assert not any("duplicate" in r.req_id for r in reqs)


def test_nasa_handbook_subsections_from_the_toc_h8():
    # regular-weight title-case subsections (often run in) count when the table of contents lists them;
    # a numbered reference list under 'REFERENCES' stays text
    lines = _spread([
        L("1. INTRODUCTION ........ 5", **_NT),
        L("1.1 Purpose ........ 5", **_NT),
        L("1.2 REFERENCES ........ 6", **_NT),
        L("2. WIDGETS ........ 7", **_NT),
        L("2.1 Widget Loads ........ 7", **_NT),
        L("1. INTRODUCTION", **_NT),
        L("1.1 Purpose. Invented prose of the purpose.", x0=99, size=12.0),
        L("1.2 REFERENCES:", **_NT),
        L("1.1 Doe, J., Invented reference one.", x0=99, size=12.0),
        L("1.3 Roe, R., Invented reference two.", x0=99, size=12.0),
        L("2. WIDGETS", **_NT),
        L("Invented prose about widgets.", **_NT),
        L("2.1 Widget Loads", x0=99, size=12.0),
        L("Invented prose about loads.", **_NT),
    ])
    reqs, _ = parse_nasa_lines(lines, "NASA-HDBK-9980", "", handbook=True)
    by = {r.req_id: r for r in reqs}
    assert list(by) == ["1.1", "1.2", "2", "2.1"]  # "1" has no prose of its own
    assert by["1.1"].text == "Invented prose of the purpose."
    assert "Invented reference two." in by["1.2"].text


def test_table_reference_word_is_case_insensitive():
    from spacestd.ecss_parser import TABLE_REF_RE
    assert TABLE_REF_RE.findall("as in table 2, and Table 4-3; see tables 5-1") == ["2", "4-3", "5-1"]
    assert TABLE_REF_RE.findall("the table of contents, a table") == []
