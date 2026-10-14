"""Gate follow-up (B8): flag in the next sentence, clause numbers, tag ranges, flagged status. Invented data."""

from types import SimpleNamespace as NS

from test_tier_flags import DOC, make_index

from spacestd.citations import CitationChecker
from spacestd.index import StandardsIndex
from spacestd.models import Document, Requirement
from spacestd_agent import StandardsAgent
from spacestd_agent.agent import flag_note


def chk():
    return CitationChecker(make_index())


def test_flag_in_the_next_sentence():
    c = chk()
    assert c.check(f"{DOC} Table 2 gives 7.25 for metallic parts. Check against the source, page 12.").ungrounded == []
    assert c.check(f"{DOC} Table 2 gives 7.25 for metallic parts. This is check against the source, page 12."
                   ).ungrounded == []
    assert c.check(f"{DOC} Table 2 gives 7.25 for metallic parts. Page 12.").ungrounded == []
    # not the next sentence, another line, or a flag sentence with numbers of its own
    assert c.check(f"{DOC} Table 2 gives 7.25. It applies to bolts. Check against the source.").unflagged == ["7.25"]
    assert c.check(f"{DOC} Table 2 gives 7.25.\nCheck against the source.").unflagged == ["7.25"]
    assert c.check(f"{DOC} Table 2 gives 7.25. Check against the source, factor 9 applies.").unflagged == ["7.25"]


def test_semicolon_inside_parenthesis_does_not_split():
    c = chk()
    ans = f"It gives 7.25 for metallic parts ({DOC}, Table 2; check against the source, page 12)."
    assert c.check(ans).ungrounded == []
    assert c.check(f"It gives 7.25 [{DOC} Table 2; page 12].").ungrounded == []
    assert c.check(f"It gives 7.25 ({DOC}, Table 2); other text; check against the source.").unflagged == ["7.25"]


def test_markdown_table_row_is_one_segment():
    c = chk()
    assert c.check(f"| {DOC} Table 2 | metallic. parts | 7.25 | check against the source, page 12 |").ungrounded == []
    assert c.check(f"{DOC} Table 2\n| a | 7.25 |\n| check against the source |").unflagged == ["7.25"]


def test_flag_on_the_line_introducing_a_table():
    c = chk()
    table = "| Material | Ultimate |\n|---|---|\n| Metallic | 7.25 |"

    def check(text):
        return c.check(text, extra_records=[f"{DOC}|Table 2"])

    for intro in (f"{DOC} Table 2 (check against the source, page 12):", "- **Check against the source, page 12:**",
                  "Values (page 12):"):
        assert check(f"{intro}\n\n{table}").ungrounded == [], intro
    # no flag line, a flag line without ":", a different page, or a later text: unflagged
    assert check(f"{DOC} Table 2:\n{table}").unflagged == ["7.25"]
    assert check(f"Check against the source, page 12.\n{table}").unflagged == ["7.25"]
    assert check(f"Values (page 99):\n{table}").unflagged == ["7.25"]
    # only the table right after the flag line: a second table after other text is not covered
    assert check("Check against the source, page 12:\n| a | 1 |\n\nText.\n\n| Metallic | 7.25 |").unflagged == ["7.25"]
    assert check(f"Check against the source:\n\nText.\n{table}").unflagged == ["7.25"]


def test_tag_ranges_are_not_values():
    c = chk()
    for ref in ("DSR 3-4", "DSR 3–4", "DSR 3 to 5", "DSR 3 and 4"):
        assert c.answer_numbers(f"Detailed requirements ({ref}) give 6") == ["6"], ref
    assert c.answer_numbers("The margin is 3 to 5") == ["3", "5"]  # no tag before it


def test_hundred_and_thousand_words_ground_numbers():
    d = Document(DOC, "", "", "", [Requirement(DOC, "", "DSR 5", "5", "A hundred per cent inspection of one thousand parts.")])
    c = CitationChecker(StandardsIndex([d]))
    assert c.check(f"{DOC} DSR 5: 100 % inspection of 1000 parts.").ungrounded == []
    assert c.check(f"{DOC} DSR 5: 100 % inspection of 10 parts.").ungrounded == ["10"]


def test_clause_numbers_are_not_values():
    c = chk()
    assert c.answer_numbers("NASA-HDBK-7005, 4.6: the interior level is 139.5 dB") == ["139.5"]
    assert c.answer_numbers("(ECSS-E-HB-32-23A Rev.1, 12.2) gives 3") == ["3"]
    assert c.answer_numbers(f"See {DOC} Rev.2, 5.1 for 3") == ["3"]
    assert c.answer_numbers("Guidance in 4.4 (guidance 1, not a requirement) and 4.5 (req 2) cover 7") == ["7"]
    assert c.answer_numbers("check the source (pages 17 and 26) for 8") == ["8"]
    assert c.answer_numbers("see pp. 12, 14 and 20; limit 1.25") == ["1.25"]
    assert c.answer_numbers("see page 52, 1.25 applies") == ["1.25"]


def test_values_next_to_citations_still_count():
    c = chk()
    assert c.answer_numbers(f"a factor of 1.4 ({DOC}, Table 2)") == ["1.4"]
    assert c.answer_numbers(f"gives 1,25 ({DOC} 4.3.1a)") == ["1.25"]
    assert c.answer_numbers(f"gives 1,25 ({DOC} DSR 4)") == ["1.25"]


def test_unflagged_sources_name_document_table_and_page():
    res = chk().check(f"{DOC} Table 2: ultimate factor 7.25.")
    assert res.unflagged_sources == {"7.25": [f"{DOC} Table 2, page 12"]}
    assert res.to_dict()["unflagged_sources"] == {"7.25": [f"{DOC} Table 2, page 12"]}


# -- agent -------------------------------------------------------------------------------------------
def text(t):
    return NS(stop_reason="end_turn", content=[NS(type="text", text=t)])


class FakeClient:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.beta = NS(messages=NS(create=lambda **kw: self.responses.pop(0)))


def get_table():
    return NS(stop_reason="tool_use",
              content=[NS(type="tool_use", id="tu1", name="get_table", input={"doc_id": DOC, "table_id": "Table 2"})])


def ask(*responses):
    return StandardsAgent(make_index(), client=FakeClient(get_table(), *responses)).ask("What is the ultimate factor?")


def test_only_unflagged_table_numbers_are_flagged_not_declined():
    bad = f"{DOC} Table 2 gives 7.25 for metallic parts."
    res = ask(text(bad), text(bad))
    assert res.status == "flagged" and res.answer.startswith(bad)
    note = f"Check against the source: 7.25 ({DOC} Table 2, page 12) comes from a table below the verified tier."
    assert res.answer.splitlines()[-1] == note
    c = chk()
    assert note == flag_note(c.check(bad, extra_records=[f"{DOC}|Table 2"]))
    assert c.check(res.answer, extra_records=[f"{DOC}|Table 2"]).ungrounded == []
    assert res.check["ungrounded"] == [] and res.to_record()["gate"]["status"] == "flagged"


def test_unretrieved_numbers_or_invented_ids_still_decline():
    worse = text(f"{DOC} Table 2 gives 7.25, or 8.5 for bolts.")
    assert ask(worse, worse).status == "declined"
    invented = text(f"{DOC} DSR 99 and Table 2 give 7.25.")
    assert ask(invented, invented).status == "declined"
