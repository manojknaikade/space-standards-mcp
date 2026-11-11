"""NASA Procedural Requirements (NPR) parser over layout lines of the NODIS PDF.

NODIS prints every NPR the same way (docs/PARSING_NOTES.md, NPR):
- a page header 'NPR 7150.2D -- Chapter2 Page 16 of 89' names the part: TOC, Preface, ChapterN, AppendixX.
  The contents part is skipped; the header lines themselves are not text;
- headings are bold: 'Chapter 2. Title', 'Appendix A. Definitions', 'Preface', '2.1 Title', 'P.1 Purpose';
- a numbered paragraph ('2.1.5.11 The Center Director ... [SWE-144]') is one record. Its ID is the requirement
  tag printed at its end when there is exactly one ('SWE-144'), else the paragraph number; `clause` is the
  paragraph number either way, so both find it. Lettered and bulleted items below it stay in its text;
- a lettered item directly under a heading (the Preface: 'P.1 Purpose', 'a. ...') is a record '<section><letter>';
- 'Note:' paragraphs (italic) attach to the record above;
- other prose under a heading is a guidance record '<section> guidance N';
- kind: 'shall' -> requirement, 'should' -> recommendation, 'may' -> permission, else guidance. Appendices
  are guidance unless they say 'shall'.
"""

from __future__ import annotations

import re
from collections import Counter

from .models import Requirement
from .parser import find_references
from .pdf_extract import Line

PAGE_HEADER_RE = re.compile(r"^NPR \d{4}\.\d+[A-Z]? -- (\S+) Page \d+ of \d+$")
FOOTER_RE = re.compile(r"verify current version|^this document (?:does not|is)|nodis library", re.I)
PART_RE = re.compile(r"^(Chapter|Appendix)\s+([0-9A-Z]{1,2})[.:]?\s*(.*)$")
SECTION_RE = re.compile(r"^((?:\d{1,2}|[A-Z]|P)(?:\.\d{1,2}){1,5})\.?\s+(\S.*)$")
PARA_RE = re.compile(r"^((?:\d{1,2}|[A-Z])(?:\.\d{1,2}){1,6})\.?\s+(\S.*)$")
LETTER_RE = re.compile(r"^([a-z])\.\s+(\S.*)$")
NOTE_RE = re.compile(r"^Note(?:\s+\d+)?\s*[:\-–]\s*(.*)$", re.I)
TAG_RE = re.compile(r"\[([A-Z]{2,6})[- ](\d{1,4})\]")
TABLE_REF_RE = re.compile(r"\bTables?\s+([A-Z]?\d+(?:-\d+)?)")


def _kind(text: str, appendix: bool) -> str:
    t = text.lower()
    if re.search(r"\bshall\b", t):
        return "requirement"
    if appendix:
        return "guidance"
    if re.search(r"\bshould\b", t):
        return "recommendation"
    if re.search(r"\bmay\b", t):
        return "permission"
    return "guidance"


def parse_npr_lines(lines: list[Line], doc_id: str, issue: str, stats: dict | None = None) -> tuple[list[Requirement], list[str]]:
    reqs: list[Requirement] = []
    seen: set[str] = set()
    guidance_n: Counter = Counter()
    path: list[str] = []
    section = ""  # number of the heading the text is under ('2.1', 'P.1', 'A')
    part = "TOC"
    appendix = False
    current: Requirement | None = None
    in_note = False
    body_words = 0
    sizes = Counter(round(ln.size) for ln in lines if ln.text and not PAGE_HEADER_RE.match(ln.text))
    body_size = sizes.most_common(1)[0][0] if sizes else 12

    def finish() -> None:
        nonlocal current, in_note
        r = current
        if r is not None:
            r.text = r.text.strip()
            tags = list(dict.fromkeys(f"{a}-{n}" for a, n in TAG_RE.findall(r.text)))
            # the tag printed at the end of a requirement is how it is cited ('SWE-144')
            if len(tags) == 1 and re.search(r"\[[A-Z]{2,6}[- ]\d{1,4}\]\.?\s*$", r.text.split("\n")[0] if "\n" in r.text and
                                              TAG_RE.search(r.text.split("\n")[0]) else r.text) and tags[0] not in seen:
                seen.discard(r.req_id)
                r.req_id = tags[0]
                seen.add(r.req_id)
            r.kind = _kind(r.text, appendix)
            r.references = find_references(" ".join([r.text, *r.notes]))
            r.tables = list(dict.fromkeys(f"Table {m}" for m in TABLE_REF_RE.findall(r.text)))
        current, in_note = None, False

    def start(req_id: str, clause: str, text: str, page: int) -> None:
        nonlocal current
        finish()
        if req_id in seen:
            req_id = f"{req_id} (duplicate {len(seen)})"
        seen.add(req_id)
        current = Requirement(doc_id, issue, req_id, clause, text, list(path), page=page)
        reqs.append(current)

    def heading(num: str, title: str, level: int) -> None:
        nonlocal section, path
        finish()
        section = num
        path = path[: level - 1] + [f"{num} {title}".strip()]

    for ln in lines:
        text = ln.text
        if not text:
            continue
        h = PAGE_HEADER_RE.match(text)
        if h:
            part = h.group(1)
            continue
        if part == "TOC" or ln.size < body_size - 2 or FOOTER_RE.search(text):
            continue
        body_words += len(text.split())
        bold = ln.bold >= 0.6 or ln.size >= body_size + 3

        if bold:
            p = PART_RE.match(text)
            s = SECTION_RE.match(text)
            if p:
                finish()  # the last record of the previous part is classified under that part
                appendix = p.group(1) == "Appendix"
                num = p.group(2)
                section, path = num, [f"{p.group(1)} {num} {p.group(3)}".strip()]
                continue
            if text.strip().lower() == "preface":
                finish()
                appendix = False
                section, path = "P", ["Preface"]
                continue
            if s:
                heading(s.group(1), s.group(2), s.group(1).count(".") + 1)
                continue
            if current is None and path:  # a wrapped heading line
                path[-1] = f"{path[-1]} {text}"
                continue

        note = NOTE_RE.match(text)
        if note and current is not None:
            current.notes.append(note.group(1))
            in_note = True
            continue
        para = PARA_RE.match(text)
        if para and not bold and (para.group(1).startswith(section.split(".")[0] + ".") or not section):
            start(para.group(1), para.group(1), para.group(2), ln.page)
            continue
        letter = LETTER_RE.match(text)
        if letter and (current is None or current.req_id.startswith(f"{section}") and current.clause == section
                       and re.fullmatch(re.escape(section) + r"[a-z]", current.req_id)):
            start(f"{section}{letter.group(1)}", section, letter.group(2), ln.page)
            continue
        if in_note and current is not None and (ln.italic >= 0.5 or not (para or letter)):
            current.notes[-1] = f"{current.notes[-1]} {text}".strip()
            continue
        in_note = False
        if current is None:
            if not section:
                continue
            guidance_n[section] += 1
            start(f"{section} guidance {guidance_n[section]}", section, text, ln.page)
            continue
        new_item = bool(letter) or text[:1] in "•▪" or bool(re.match(r"^\(\d{1,2}\)\s", text))
        current.text = f"{current.text}\n{text}" if new_item else f"{current.text} {text}"

    finish()
    if stats is not None:
        stats.update(body_words=body_words, unparsed_words=0)
    return reqs, []
