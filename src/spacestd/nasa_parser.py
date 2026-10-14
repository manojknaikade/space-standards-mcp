"""NASA technical standard parser (NASA-STD-5001B, NASA-STD-5019A) over PDF layout lines.

Rules (docs/PARSING_NOTES.md):
- body only: from section 4 to 'APPENDIX A' (the compliance matrix repeats every tag);
- a bracketed tag ([FSR 24], [FCR 11]) is a *definition* only when it starts a paragraph
  (optionally after 'a.', '(1)' or a section number); elsewhere it is a cross-reference;
- untagged lettered items directly under a tagged paragraph belong to it (FCR 6 a-c);
- italic paragraphs are guidance (kind 'guidance'); '[Rationale: ...]' attaches to the
  requirement as a note;
- 5019A: a section that says it implements an FCR ('... to meet requirement [FCR 11]
  section 7.2.a') makes its lettered items citable units: 'FCR 11 / 7.2.1.a';
- tag prefixes may end in a digit ('[V2 6001]', NASA-STD-3001 Vol 2);
- a section number before a lead tag may end in a dot ('4.4.1.1. [PVTR 15]', NASA-STD-7001C; H5);
- a body with no tag definitions (older standards, the 87xx series; PARSING_NOTES H2) is
  'tagless': each lettered, numbered or plain paragraph with 'shall' that no tag owns becomes
  a requirement '4.2a', '4.3(1)' or '4.4 req 1' (section + item, or the n-th 'shall' paragraph).
- body start: the first bold '4 Title' / '4.0 Title' heading, else the first bold numbered heading, else
  the whole text, so nothing is dropped silently (H6: a document without a section-4 heading gave nothing).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .ecss_parser import TABLE_REF_RE
from .models import Requirement
from .parser import find_references
from .pdf_extract import Line

PREFIX = r"(?:[A-Z]{2,6}|[A-Z]{1,5}\d)"  # FSR, FCR; V2 (NASA-STD-3001 Vol 2)
TAG_RE = re.compile(rf"\[({PREFIX})[ -]?(\d{{1,4}})\]")
# a section number may carry a short heading before the tag: '4.4 Gadget logs [V7 1234] Each ...',
# and a trailing dot: '4.4.1.1. [PVTR 15] ...' (NASA-STD-7001C; PARSING_NOTES H5)
LEAD_TAG_RE = re.compile(r"^(?:(?P<sec>\d+(?:\.\d+)+)\.?\s+(?:(?P<title>[A-Z][^\[\].,;:]{0,60}?)\s+)?|(?P<let>[A-Za-z])\.\s+|\((?P<num>\d{1,2})\)\s+)?"
                         rf"\[(?P<tag>{PREFIX})[ -]?(?P<n>\d{{1,4}})\]\s*(?P<rest>.*)$")
NUMBER_ONLY_RE = re.compile(r"^\d{1,2}(?:\.\d{1,2}){1,5}\.?$")
SECTION_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,5})\.?\s+(\S.*)$")
LETTER_RE = re.compile(r"^([a-z])\.\s+(\S.*)$")
# sub-items: '(1)', '(a)', bullets, and the third level under '(n)': 'A.' and roman 'ii.'
# ('i.' alone is also a letter item; the indentation check in parse_nasa_lines sorts it out)
SUBITEM_RE = re.compile(r"^(?:\(\d{1,2}\)|\([a-z]\)|[•▪]|[A-H]\.(?=\s)|(?:ii|iii|iv|vi{0,3}|ix|x)\.(?=\s))\s*\S")
NUM_RE = re.compile(r"^(?:(\d{1,2})\.|\((\d{1,2})\))\s+(\S.*)$")  # tagless numbered items: '1.', '(1)'
SHALL_RE = re.compile(r"\bshall\b")
STATEMENT_RE = re.compile(r"\b(?:shall|must)\b")  # a requirement outside FCR-style sections (B3: no false record had one)
DELETED_RE = re.compile(r"^Deleted\b", re.I)
DOTNUM_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,5})\.?\s+(\S.*)$")  # tagless numbered paragraph: '4.3.1 The ...'
DOTNUM_START_RE = re.compile(r"^\d{1,2}(?:\.\d{1,2}){1,5}\.?\s+[A-Z]")
CAPTION_LINE_RE = re.compile(r"^(?:Table|Figure)\s+[A-Z]?\d+(?:[-.]\d+)*\s*[\u2014\u2013:-]")
CONTEXT_RE = re.compile(rf"\[(?P<tag>{PREFIX})[ -]?(?P<n>\d{{1,4}})\],?\s*(?:section\s*)?(?P<sec>\d+(?:\.\d+)*(?:\.[a-z])?)?")


@dataclass
class _Para:
    lines: list[Line] = field(default_factory=list)

    @property
    def text(self) -> str:
        out = ""
        for ln in self.lines:
            if out.endswith("-") and len(out) > 1 and out[-2].isalnum():
                out += ln.text
            else:
                out = f"{out} {ln.text}" if out else ln.text
        return out

    @property
    def italic(self) -> bool:
        ink = sum(len(ln.text) for ln in self.lines) or 1
        return sum(len(ln.text) * ln.italic for ln in self.lines) / ink >= 0.6

    @property
    def page(self) -> int:
        return self.lines[0].page


def _bold(ln: Line) -> bool:
    """Bold, or mostly bold with a trademark glyph in another font ('4.7.3 Title(R)'; H13c)."""
    return ln.is_bold or (ln.bold >= 0.6 and ln.text.rstrip().endswith(("\u00ae", "\u2122", "\u00a9")))


def _caps_heading(ln: Line, left: float | None) -> bool:
    """Handbook heading set in regular weight: '2. DEFINITIONS', '1.3 REFERENCES:' (H8). Table-of-contents
    lines (dot leaders, trailing page number) are not headings."""
    m = SECTION_RE.match(ln.text)
    if not m or _bold(ln) or TAG_RE.search(ln.text):
        return False
    title = m.group(2)
    if re.search(r"\.{3,}|(?:\.\s){3,}", title) or re.search(r"\s\d+$", title) or len(title.split()) > 15:
        return False
    letters = [c for c in title if c.isalpha()]
    if len(letters) < 3 or sum(c.isupper() for c in letters) < 0.8 * len(letters):
        return False
    return left is None or ln.x0 <= left + 3


def _is_heading(ln: Line, handbook: bool = False, left: float | None = None) -> bool:
    if _bold(ln):
        return bool(SECTION_RE.match(ln.text)) and not TAG_RE.search(ln.text) and "...." not in ln.text
    return handbook and _caps_heading(ln, left)


def _plausible_next(num: str, cur: str) -> bool:
    """`num` is a child of `cur` or the next sibling of `cur` or of one of its parents."""
    p, c = num.split("."), cur.split(".")
    if not cur:
        return False
    if len(p) == len(c) + 1 and p[: len(c)] == c:
        return True
    return any(len(p) == k and p[: k - 1] == c[: k - 1] and p[k - 1].isdigit() and c[k - 1].isdigit()
               and int(p[k - 1]) == int(c[k - 1]) + 1 for k in range(1, len(c) + 1))


TOC_LINE_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,5})\.?\s+\S.*?(?:\.{3,}|(?:\.\s){3,}|\s)\s*\d{1,3}\s*$")


def toc_numbers(lines: list[Line]) -> set[str]:
    """Section numbers listed in the table of contents (dot leaders or a trailing page number)."""
    return {m.group(1) for ln in lines if (m := TOC_LINE_RE.match(ln.text))}


def _toc_heading(ln: Line, cur: str, toc: set[str]) -> tuple[Line, Line | None] | None:
    """Handbook subsection heading in regular weight and title case, often run in ('2.2.1 Title. Prose ...';
    NASA-HDBK-7005, H8): taken when its number is in the table of contents and is the plausible next section,
    so numbered reference lists ('1.4 Author, ...' under '1.3 REFERENCES') stay text. Returns the heading
    (marked bold from here on) and the run-in prose, if any."""
    m = SECTION_RE.match(ln.text)
    if not m or _bold(ln) or TAG_RE.search(ln.text) or m.group(1) not in toc or not _plausible_next(m.group(1), cur):
        return None
    title, rest = m.group(2), ""
    k = title.find(". ")
    if 0 < k and len(title[:k].split()) <= 12:
        title, rest = title[:k], title[k + 2:].strip()
    head = Line(**{**ln.__dict__, "text": f"{m.group(1)} {title}", "bold": 1.0})
    return head, (Line(**{**ln.__dict__, "text": rest}) if rest else None)


def _italic_heading(ln: Line, cur: str, hx: float) -> bool:
    """A heading set in italic, not bold, at the heading margin (H13c): short, no 'shall', a plausible next number."""
    m = SECTION_RE.match(ln.text)
    if not m or _bold(ln) or not ln.is_italic or TAG_RE.search(ln.text) or abs(ln.x0 - hx) > 3:
        return False
    t = ln.text.rstrip()
    return not t.endswith(".") and "...." not in t and not SHALL_RE.search(t) and len(t.split()) < 12 \
        and _plausible_next(m.group(1), cur)


def _starts_block(ln: Line, numbered: bool = False) -> bool:
    t = ln.text
    return bool(LEAD_TAG_RE.match(t) or LETTER_RE.match(t) or SUBITEM_RE.match(t) or t.startswith("[Rationale")
                or (numbered and (NUM_RE.match(t) or DOTNUM_START_RE.match(t))))


def _complete(text: str) -> bool:
    t = text.rstrip()
    return t.endswith((".", ":", ";", ")", "]")) or t.endswith((" and", " or"))


def _join_split_numbers(lines: list[Line]) -> list[Line]:
    """A bold heading number extracted as a line of its own, with its bold title beside it a few points lower
    (5018 '4.7.3' + 'Title®': the superscript shifts the title's baseline), becomes one heading line (H13c)."""
    out: list[Line] = []
    for ln in lines:
        prev = out[-1] if out else None
        if prev is not None and NUMBER_ONLY_RE.match(prev.text) and _bold(prev) and _bold(ln) and ln.page == prev.page \
                and ln.x0 > prev.x0 and abs(ln.top - prev.top) < ln.size / 2:
            out[-1] = Line(**{**prev.__dict__, "text": f"{prev.text} {ln.text}", "bottom": max(prev.bottom, ln.bottom)})
            continue
        out.append(ln)
    return out


def paragraphs(lines: list[Line], numbered: bool = False, handbook: bool = False, left: float | None = None,
               hx: float = 72.0, toc: set[str] | None = None) -> list[_Para | Line]:
    """Group body lines into paragraphs; headings are returned as single Line items.

    A line opening with a tag or a list marker starts a new block only after a
    complete line: '...to meet requirement' + '[FCR 21].' is one sentence.
    `numbered`: '1.' also opens a block (tagless documents only, so tagged ones keep their grouping).
    """
    out: list[_Para | Line] = []
    cur: _Para | None = None
    prev: Line | None = None
    cur_sec = ""
    for ln in _join_split_numbers(lines):
        if not ln.text:
            continue
        if toc and (split := _toc_heading(ln, cur_sec, toc)):
            head, rest = split
            out.append(head)
            cur, prev = None, head
            cur_sec = SECTION_RE.match(head.text).group(1)
            if rest is None:
                continue
            ln = rest  # run-in prose opens the section's first paragraph
        if _italic_heading(ln, cur_sec, hx):
            ln = Line(**{**ln.__dict__, "bold": 1.0})  # an italic heading counts as a heading from here on
        if _is_heading(ln, handbook, left) or (_bold(ln) and LETTER_RE.match(ln.text) and not TAG_RE.search(ln.text)):
            out.append(ln)
            cur, prev = None, ln
            m = SECTION_RE.match(ln.text)
            if m and _is_heading(ln, handbook, left):
                cur_sec = m.group(1)
            continue
        if _bold(ln) and isinstance(out[-1:] and out[-1], Line) and prev is out[-1] and ln.page == prev.page \
                and ln.top - prev.bottom < ln.size:
            out[-1] = Line(**{**prev.__dict__, "text": f"{prev.text} {ln.text}", "bottom": ln.bottom})
            prev = out[-1]
            continue  # wrapped heading
        if cur is not None and prev is not None and ln.page == prev.page and len(ln.text.strip()) <= 2 \
                and ln.text.strip().isalpha():
            cur.lines.append(ln)  # a subscript set on a line of its own ('K' + 't'): not a paragraph, and
            continue  # not the line a list item follows (5017B DDMR 46 a. / b.)
        gap = prev is not None and ln.page == prev.page and ln.top - prev.bottom > 0.6 * ln.size
        new = cur is None or bool(CAPTION_LINE_RE.match(ln.text)) or (
            _starts_block(ln, numbered) and (prev is None or gap or _complete(prev.text)
                                             or bool(CAPTION_LINE_RE.match(prev.text))))
        if not new and prev is not None:
            # a switch to or from italic (guidance) opens a paragraph, except on a partly italic line after an
            # incomplete one: 7003A sets a requirement's tail and its italic guidance on one line
            # ('... testing shall be performed. A test early in ...')
            mixed = 0.05 < ln.italic < 0.95 and not _complete(prev.text)
            new = gap or (ln.is_italic != prev.is_italic and not mixed)
        if new:
            cur = _Para()
            out.append(cur)
        cur.lines.append(ln)
        prev = ln
    return out


def parse_nasa_lines(lines: list[Line], doc_id: str, issue: str, handbook: bool = False,
                     stats: dict | None = None) -> tuple[list[Requirement], list[str]]:
    """Return requirement/guidance records and unparsed body paragraphs. `stats`, when given, receives
    `unparsed_words` and `body_words` (words of the body lines) for the health report."""
    # body: first section-4 heading after the table of contents (else the first numbered heading, else
    # everything: H6), up to Appendix A
    xs = [round(ln.x0) for ln in lines if ln.text]
    left = max(set(xs), key=xs.count) if xs else None  # left margin: the commonest x0
    start = next((i for i, ln in enumerate(lines) if _is_heading(ln) and re.match(r"^4(?:\.0)?\.?\s+[A-Z]", ln.text)),
                 None)
    if start is None:
        start = next((i for i, ln in enumerate(lines) if _is_heading(ln, handbook, left)), 0)
    elif handbook:  # plain upper-case headings (H8) may start before section 4
        cap = next((i for i, ln in enumerate(lines) if _caps_heading(ln, left)), None)
        start = min(start, cap) if cap is not None else start
    end = next((i for i in range(start, len(lines)) if _bold(lines[i]) and lines[i].text.upper().startswith("APPENDIX")),
               len(lines))
    body = lines[start:end]
    tagless = not any(LEAD_TAG_RE.match(ln.text) for ln in body)
    hxs = [round(ln.x0) for ln in body if _is_heading(ln, handbook, left)]
    hx = max(set(hxs), key=hxs.count) if hxs else (left or 72.0)
    toc = toc_numbers(lines[:start]) if handbook else None
    paras = paragraphs(body, numbered=tagless, handbook=handbook, left=left, hx=hx, toc=toc)

    reqs: list[Requirement] = []
    by_id: dict[str, Requirement] = {}
    unparsed: list[str] = []
    section, path = "", []
    context: dict[str, str] = {}  # section -> "FCR 11" (tag the section implements)
    explicit: set[str] = set()  # sections whose context comes from a 'to meet requirement [FCR 11]' sentence
    guidance_n: dict[str, int] = {}
    shall_n: dict[str, int] = {}  # tagless 'shall' paragraphs per section
    unparsed_words = 0
    current: Requirement | None = None
    attach_items = False  # untagged lettered items still belong to the current tagged requirement
    tag_req: Requirement | None = None  # last tagged requirement, and the last list letter it holds
    tag_letter = ""
    owner: Requirement | None = None  # last non-guidance record: where list items go after guidance

    def ctx_for(sec: str) -> str:
        return ctx_key(sec)[0]

    def ctx_key(sec: str) -> tuple[str, str]:
        parts = sec.split(".")
        for k in range(len(parts), 0, -1):
            tag = context.get(".".join(parts[:k]))
            if tag:
                return tag, ".".join(parts[:k])
        return "", ""

    def add(req: Requirement) -> Requirement:
        nonlocal owner
        if req.kind != "guidance":
            owner = req
        if req.req_id in by_id:
            req.req_id = f"{req.req_id} (duplicate)"
            req.flags.append("tag defined twice in the body")
        by_id[req.req_id] = req
        reqs.append(req)
        return req

    def set_section(sec: str, title: str) -> None:
        nonlocal section, path, current, attach_items, tag_req, tag_letter
        section = sec
        tag_req, tag_letter = None, ""
        level = sec.count(".") + 1
        path = path[: level - 1] + [f"{sec} {title}".strip()]
        current, attach_items = None, False

    letter_xs = [round(p.lines[0].x0) for p in paras if isinstance(p, _Para) and LETTER_RE.match(p.text)]
    letter_x = max(set(letter_xs), key=letter_xs.count) if letter_xs else None

    for item in paras:
        if isinstance(item, Line):
            m = SECTION_RE.match(item.text)
            if m and _is_heading(item, handbook, left):
                set_section(m.group(1), m.group(2))
            else:  # bold lettered sub-heading, e.g. 5001B '4. a. General'
                path = path[: section.count(".") + 1] + [item.text]
                current, attach_items = None, False
            continue

        text = item.text
        if re.match(r"^(Table|Figure)\s+[A-Z]?\d+", text):
            continue  # captions; tables are extracted separately
        lead = LEAD_TAG_RE.match(text)
        lead_key = f"{lead.group('tag')} {lead.group('n')}" if lead else ""
        fresh = lead is not None and lead_key not in by_id
        is_deleted = fresh and bool(DELETED_RE.match(lead.group("rest")))
        is_tagged_req = fresh and bool(SHALL_RE.search(lead.group("rest")))
        # a numbered paragraph that opens upright and holds 'shall' is a record even when italic guidance
        # fills most of it (7003A 4.1.1: the requirement's tail and the guidance share a line)
        dot0 = DOTNUM_RE.match(text) if tagless and not item.lines[0].is_italic else None
        upright_req = bool(dot0 and section and dot0.group(1).startswith(section + ".") and SHALL_RE.search(text))
        if item.italic and not (is_tagged_req or is_deleted or upright_req):  # a tagged paragraph in an italic block is a record
            if text.startswith("[Rationale") and current is not None:
                current.notes.append(text.strip("[]"))
                continue
            n = guidance_n.get(section, 0) + 1
            guidance_n[section] = n
            current = add(Requirement(doc_id, issue, f"{section} guidance {n}", section, text, list(path),
                                      kind="guidance", page=item.page))
            attach_items = False
            continue

        if is_tagged_req or is_deleted:
            if lead.group("sec"):
                set_section(lead.group("sec"), lead.group("title") or "")
            tag = lead_key
            if is_deleted:  # '[WDG 7] Deleted Requirement': kept so the lookup explains the gap (H12)
                current = add(Requirement(doc_id, issue, tag, section, lead.group("rest"), list(path), kind="deleted",
                                          page=item.page))
                tag_req, attach_items = None, False
                continue
            let = lead.group("let") or ""
            clause = section + (let if let.islower() else "")
            current = add(Requirement(doc_id, issue, tag, clause, lead.group("rest"), list(path), page=item.page))
            tag_req, tag_letter = current, "`"  # '`' precedes 'a'
            context.setdefault(section, tag)
            attach_items = True
            continue

        letter = LETTER_RE.match(text)
        if letter and letter.group(1) in "ivx" and letter_x is not None and abs(round(item.lines[0].x0) - letter_x) > 6:
            letter = None  # deeper-indented 'i.' / 'v.' items are roman numerals inside an item
            # (other letters keep their role at any indent: 5019A 6.2.5 sets 'a.'/'b.' at x = 90)
        sub = SUBITEM_RE.match(text) or (LETTER_RE.match(text) and not letter)
        if letter and tag_req is not None and tag_req.clause.startswith(section) and tag_letter \
                and letter.group(1) == chr(ord(tag_letter) + 1):
            # the tagged requirement's own list resumes after a guidance paragraph (FCR 9 c. -> d.)
            tag_req.text = f"{tag_req.text}\n{text}"
            tag_letter, current, attach_items = letter.group(1), tag_req, True
            continue
        if sub and current is not None and current.kind == "guidance" and owner is not None \
                and owner.clause.startswith(section):
            # a list resumes after an italic guidance paragraph: the items belong to the
            # requirement the list started in, not to the guidance (5019A 6.1.1.4 '(4)', 7.2.6 '(1)')
            current = owner
        if current is not None and (sub or (letter and attach_items)):
            current.text = f"{current.text}\n{text}"
            if letter and current is tag_req:
                tag_letter = letter.group(1)
            continue

        refs = list(CONTEXT_RE.finditer(text))
        if letter:
            tag = ctx_for(section)
            if tag:
                rid = f"{tag} / {section}.{letter.group(1)}"
                current = add(Requirement(doc_id, issue, rid, section, letter.group(2), list(path), parent=tag,
                                          page=item.page))
                attach_items = False
                continue
        elif refs and re.search(r"\b(requirement|meet|satisfy|comply)\b", text, re.I):
            tag = f"{refs[0].group('tag')} {refs[0].group('n')}"
            if not context.get(section):
                context[section] = tag
            explicit.add(section)
            current = add(Requirement(doc_id, issue, f"{tag} / {section}", section, text, list(path), parent=tag,
                                      page=item.page))
            attach_items = False
            continue
        elif current is not None and text[:1].islower():
            current.text = f"{current.text} {text}"  # sentence continued after a page break
            continue
        tag, tag_sec = ctx_key(section)
        if tag and not lead:
            rid = f"{tag} / {section}"
            if rid in by_id:  # more lead-in text of the same section
                by_id[rid].text += "\n" + text
                current = by_id[rid]
                attach_items = False
                continue
            if tag_sec in explicit or STATEMENT_RE.search(text):  # FCR-style section text, or a real statement
                current = add(Requirement(doc_id, issue, rid, section, text, list(path), parent=tag, page=item.page))
                attach_items = False
                continue
            if tag_req is not None and tag_req.clause.startswith(section) and tag_letter not in ("", "`"):
                tag_req.text = f"{tag_req.text}\n{text}"  # an unlettered entry closing the tagged record's list
                current, attach_items = tag_req, True
                continue
            # equation, footnote, figure label, NOTE or sentence tail (H12): falls through as prose, not a record
        if handbook and section:  # handbook prose: one guidance record per numbered section (A5)
            sec = by_id.get(section)
            if sec is None:
                sec = add(Requirement(doc_id, issue, section, section, text, list(path), kind="guidance", page=item.page))
            else:
                sec.text = f"{sec.text}\n{text}"
            current, attach_items = sec, False
            continue
        if tagless and section and SHALL_RE.search(text):
            num = NUM_RE.match(text)
            dot = DOTNUM_RE.match(text)
            if dot and dot.group(1).startswith(section + "."):  # numbered paragraph '4.3.1 The ...' (H9)
                rid, body_text = dot.group(1), dot.group(2)
            elif letter:
                rid, body_text = f"{section}{letter.group(1)}", letter.group(2)
            elif num:
                rid, body_text = f"{section}({num.group(1) or num.group(2)})", num.group(3)
            else:
                n = shall_n.get(section, 0) + 1
                shall_n[section] = n
                rid, body_text = f"{section} req {n}", text
            current = add(Requirement(doc_id, issue, rid, section, body_text, list(path), page=item.page))
            # a lead-in ending in ':' owns the lettered list below it; a lettered item's own siblings do not
            attach_items = not letter and text.rstrip().endswith(":")
            continue
        if tagless and section and not (letter or sub) and TABLE_REF_RE.search(text):
            # an upright lead-in paragraph with no 'shall' that points at a table (7003A 4.3): guidance, so
            # the table is reachable from it; other tagless prose without 'shall' stays unparsed
            n = guidance_n.get(section, 0) + 1
            guidance_n[section] = n
            current = add(Requirement(doc_id, issue, f"{section} guidance {n}", section, text, list(path),
                                      kind="guidance", page=item.page))
            attach_items = False
            continue
        unparsed.append(f"{section}: {text[:120]}")
        unparsed_words += len(text.split())

    for r in reqs:
        r.text = r.text.strip()
        r.references = find_references(" ".join([r.text, *r.notes]))
        r.tables = list(dict.fromkeys(f"Table {m}" for m in TABLE_REF_RE.findall(r.text)))
    if stats is not None:
        stats.update(unparsed_words=unparsed_words, body_words=sum(len(ln.text.split()) for ln in body))
    return reqs, unparsed
