"""ECSS requirement parser over layout lines (PDF) or rendered Word paragraphs.

Rules (docs/PARSING_NOTES.md):
- requirements live in chapters >= 4 and in annexes; chapters 1-3 (scope, references,
  terms, nomenclature) and the bibliography are skipped;
- headings: numbered clauses up to five levels, chapter number printed on its own line,
  'Annex X (normative|informative)', annex clauses 'A.2.1';
- requirement = clause + letter, letters restart per clause (the PDF prints them
  correctly; for Word they are recomputed because Word runs them on: r., aa., ...);
- machine IDs (ECSS-E-ST-32-10_0110001) precede the requirement, table or figure they label;
- NOTEs attach to the requirement; nested list items (1., (a), bullets) stay inside it;
- '<<deleted>>' placeholders are kept with kind 'deleted'.
- a heading-font line without a number, followed by items restarting at 'a.', is a heading whose
  number is missing from the text layer (H1): it gets the next free number at its level and the
  records under it are flagged 'inferred clause number'.
- a bold heading-font line at body size whose number is the next free child of the current clause
  (or of one of its parents) is a heading too (H7, E-HB-32-24A level-4 headings);
- body text that becomes no record (prose paragraphs between headings and lists) is returned as
  unparsed fragments, like the NASA parser, and the body's word count goes into `stats` (H6).
- handbooks (`handbook=True`, set by the loaders from the doc_id, A5): that prose is kept instead, as one `guidance` record per numbered
  section (req_id = the clause number, paragraphs separated by newlines); no fragments are left over.
"""

from __future__ import annotations

import re
from collections import Counter

from .models import Requirement, Table
from .parser import find_references
from .pdf_extract import Line

CLAUSE_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,5})\.?\s+(\S.*)$")
CHAPTER_ONLY_RE = re.compile(r"^(\d{1,2})$")
ANNEX_RE = re.compile(r"^Annex\s+([A-Z])\s*\((normative|informative)\)\s*(.*)$", re.I)
ANNEX_CLAUSE_RE = re.compile(r"^([A-Z](?:\.\d{1,2}){1,5})\s+(\S.*)$")
DRD_RE = re.compile(r"^<(\d{1,2}(?:\.\d{1,2}){0,3})>\s*(\S.*)?$")  # DRD content headings: <5.2> Modelling assumption
MACHINE_ID_RE = re.compile(r"^(ECSS-[A-Z]-[A-Z]{2}-\d{2}(?:-\d{2})?)_(\d{6,8})$")
ITEM_RE = re.compile(r"^([a-z]{1,3})\.\s+(\S.*)$")
NOTE_RE = re.compile(r"^NOTE(?:\s+(\d{1,2}))?(?:\s*[:\-–])?(?:\s+(\S.*))?$")
LIST_RE = re.compile(r"^(?:\d{1,2}\.|\([a-z0-9]{1,3}\)|[•▪–o\-])\s+\S")
CAPTION_RE = re.compile(r"^(Table|Figure)\s+([A-Z]?\d+(?:-\d+)?)\s*:")
TABLE_REF_RE = re.compile(r"\b(?i:tables?)\s+([A-Z]?\d+-\d+|\d+)")
STALE_REF_RE = re.compile(r"\b1\.1\.1(?:\.\d{1,2})?[a-z]{0,3}\b")
DELETED_RE = re.compile(r"[<>]{2}\s*deleted", re.I)  # '>>deleted>>' is a source typo (10-03C)
CAN_RE = re.compile(r"\bcan(?:not)?\b", re.I)
EQ_NUMBER_RE = re.compile(r"^[\d\s.]*$")  # a 'title' of digits only: an equation number printed twice ('2 2')


def classify(text: str, informative: bool) -> str:
    t = text.lower()
    if DELETED_RE.match(text.strip()):
        return "deleted"
    if informative:
        return "guidance"
    if re.search(r"\bshall\b", t):
        return "requirement"
    if re.search(r"\bshould\b", t):
        return "recommendation"
    if re.search(r"\bmay\b|\bneed not\b", t):
        return "permission"
    if CAN_RE.search(t):  # possibility or capability (ECSS verbal forms), no obligation
        return "guidance"
    return "requirement"


def _letters(n: int) -> str:
    """0 -> a, 25 -> z, 26 -> aa, 27 -> bb (ECSS doubles the letter after z)."""
    return chr(ord("a") + n % 26) * (n // 26 + 1)


def _is_list(text: str, before: str) -> bool:
    """A list marker starts a new item only after a complete line ('...:', '...;', '... or').

    Avoids splitting 'at least four' + '(4) times in sequence'."""
    if not LIST_RE.match(text):
        return False
    b = before.rstrip()
    if text[0] in "•▪":
        return True
    return not b or b.endswith((":", ";", ".", ",", " or", " and", ")"))


def _join(a: str, b: str) -> str:
    if not a:
        return b
    if a.endswith("-") and len(a) > 1 and a[-2].isalnum():
        return a + b
    return f"{a} {b}"


class _Builder:
    def __init__(self, doc_id: str, issue: str, recompute_letters: bool, handbook: bool = False):
        self.doc_id, self.issue = doc_id, issue
        self.handbook = handbook
        self.section: Requirement | None = None  # handbook: the current section's prose record
        self.last: Line | None = None  # handbook: last prose line added to it
        self.recompute = recompute_letters
        self.reqs: list[Requirement] = []
        self.seen: set[str] = set()
        self.sections: dict[str, Requirement] = {}  # handbook: clause -> its section record
        self.clause = ""
        self.path: list[str] = []
        self.informative = False
        self.current: Requirement | None = None
        self.in_note = False
        self.note_x = 0.0
        self.letter_count: Counter = Counter()
        self.pending_mid = ""
        self.base_clause = ""  # clause holding DRD content headings (<n>)
        self.table_info: dict[str, tuple[str, str]] = {}  # table id -> (clause, machine id)
        self.numbered = ""  # last heading whose number is in the text
        self.level_style: dict[tuple, int] = {}  # heading style -> clause depth, from numbered headings
        self.level3_sizes: Counter = Counter()  # font size of the numbered bold level-3 headings (H13a)
        self.children: Counter = Counter()  # parent clause -> highest child number seen
        self.inferred = False
        self.glossary = False  # handbook: inside a glossary chapter (terms become records)
        self.terms: set[str] = set()

    def finish(self) -> None:
        req = self.current
        if req is not None:
            req.text = req.text.strip()
            req.kind = classify(req.text, self.informative or self.handbook)
            joined = " ".join([req.text, *req.notes])
            req.references = find_references(joined)
            req.tables = list(dict.fromkeys(f"Table {m}" for m in TABLE_REF_RE.findall(req.text)))
            for m in STALE_REF_RE.findall(joined):
                req.references = [r for r in req.references if r != m]
                flag = f"stale Word cross-reference '{m}' (field not updated in the source)"
                if flag not in req.flags:
                    req.flags.append(flag)
        self.current = self.section = self.last = None
        self.in_note = False

    def heading(self, clause: str, title: str, level: int, style: tuple | None = None) -> None:
        self.finish()
        self.clause = clause
        self.path = self.path[: level - 1] + [f"{clause} {title}".strip()]
        self.pending_mid = ""
        self.inferred = False
        if re.fullmatch(r"[A-Z0-9]\d?(?:\.\d{1,2})+", clause):
            parent, num = clause.rsplit(".", 1)
            self.children[parent] = max(self.children[parent], int(num))
        if style is not None:
            self.numbered = clause
            self.level_style.setdefault(style, clause.count(".") + 1)
            head = clause.split(".")[0]
            if clause.count(".") == 2 and style[2] and not (head.isdigit() and int(head) < 4):  # body only (terms: 3.2.1)
                self.level3_sizes[style[1]] += 1

    def level3_size(self) -> float | None:
        """Commonest font size of the numbered level-3 bold headings seen so far (a few odd ones, e.g. 11 pt
        level-3 headings in 10-03C, must not hide 12 pt level-4 headings)."""
        return self.level3_sizes.most_common(1)[0][0] if self.level3_sizes else None

    def infer_heading(self, title: str, style: tuple, depth: int | None = None) -> None:
        """Number a heading printed without its number: next child at the depth its style has
        shown on numbered headings, else next child of the last numbered clause. `depth` (H13a) is
        given when the font size alone puts the heading one step below the level-3 headings."""
        parts = self.numbered.split(".")
        depth = depth or self.level_style.get(style, len(parts) + 1)
        parent = ".".join(parts[: max(depth - 1, 1)])
        clause = f"{parent}.{self.children[parent] + 1}"
        self.heading(clause, title, clause.count(".") + 1)
        self.inferred = True

    def start(self, letter: str, text: str, page: int | None) -> None:
        self.finish()
        if self.recompute:
            letter = _letters(self.letter_count[self.clause])
        self.letter_count[self.clause] += 1
        req_id = f"{self.clause}{letter}"
        if req_id in self.seen:  # never emit two records with one ID
            req_id = f"{req_id} (duplicate {self.letter_count[self.clause]})"
        self.seen.add(req_id)
        self.current = Requirement(
            self.doc_id, self.issue, req_id, self.clause, text, list(self.path),
            machine_id=self.pending_mid, page=page,
        )
        if self.inferred:
            self.current.flags.append("inferred clause number")
        self.pending_mid = ""
        self.reqs.append(self.current)

    def start_term(self, term: str, text: str, page: int | None) -> None:
        self.finish()
        req_id = f"{self.clause}:{term}"
        if req_id in self.seen:
            req_id = f"{req_id} (duplicate {len(self.seen)})"
        self.seen.add(req_id)
        self.current = Requirement(self.doc_id, self.issue, req_id, self.clause, text, list(self.path), page=page,
                                   flags=["glossary term"])
        self.reqs.append(self.current)

    def start_section(self, text: str, page: int | None) -> None:
        req_id = self.clause
        if (sec := self.sections.get(req_id)) is not None:  # prose resumes after a NOTE, list or table
            sec.text = f"{sec.text}\n{text}"
            self.current = self.section = sec
            return
        if req_id in self.seen:
            req_id = f"{req_id} (duplicate {len(self.seen)})"
        self.seen.add(req_id)
        self.current = self.section = Requirement(self.doc_id, self.issue, req_id, self.clause, text, list(self.path),
                                                  machine_id=self.pending_mid, page=page)
        if self.inferred:
            self.current.flags.append("inferred clause number")
        self.pending_mid = ""
        self.sections[self.clause] = self.current
        self.reqs.append(self.current)


def parse_ecss_lines(lines: list[Line], doc_id: str, issue: str, *, recompute_letters: bool = False, handbook: bool = False,
                     table_lines: dict[int, str] | None = None,
                     stats: dict | None = None) -> tuple[list[Requirement], dict[str, tuple[str, str]]]:
    """Parse ECSS layout lines into requirement records.

    Returns the records and, per table caption seen, (clause, machine ID). `stats`, when given, receives
    `unparsed` (body paragraphs that became no record, '<clause>: <first 120 chars>'), `unparsed_words`
    and `body_words` (words of the body lines: chapters >= 4 and annexes, tables excluded) for the health report.
    """
    table_lines = table_lines or {}
    unparsed: list[str] = []
    frag: list[Line] = []  # prose lines of the current unparsed paragraph
    frag_clause = ""
    counts = {"body": 0, "unparsed": 0}

    def flush() -> None:
        if frag:
            text = " ".join(ln.text for ln in frag)
            unparsed.append(f"{frag_clause}: {text[:120]}")
            counts["unparsed"] += len(text.split())
            frag.clear()

    b = _Builder(doc_id, issue, recompute_letters, handbook)
    plain = [ln for ln in lines if not ln.is_bold] or lines
    body_size = Counter(round(ln.size) for ln in plain).most_common(1)[0][0] if plain else 10
    item_x = Counter(round(ln.x0) for ln in lines if ITEM_RE.match(ln.text)).most_common(1)
    item_x = item_x[0][0] if item_x else 0
    body_font = Counter(ln.font.split("-")[0] for ln in plain).most_common(1)[0][0] if plain else ""

    def heading_font(ln: Line) -> bool:
        return ln.size >= body_size + 0.9 and bool(body_font) and not ln.font.startswith(body_font)

    def equation_number(ln: Line) -> bool:
        """A line like '2 2' (an equation number printed twice, H14) is no heading: its 'title' is only digits,
        or its chapter goes back to an earlier one than the clause being read."""
        m = CLAUSE_RE.match(ln.text)
        if not m or ln.is_bold and not EQ_NUMBER_RE.match(m.group(2)):
            return False
        if EQ_NUMBER_RE.match(m.group(2)):
            return True
        cur = b.clause.split(".")[0]
        return cur.isdigit() and int(m.group(1).split(".")[0]) < int(cur)

    def is_heading(ln: Line) -> bool:
        if ln.size >= body_size + 1.5 and ln.is_bold:
            return True
        # DRD item headings may be set at body size (H13b); their '<' '>' are often not bold (10-03C: 0.79)
        if ln.size >= body_size - 0.9 and (ln.bold >= 0.6 or heading_font(ln)) and DRD_RE.match(ln.text):
            return True
        # five-level clause headings: slightly larger, non-bold, in the heading font (32-01: ArialMT 11)
        return heading_font(ln) and bool(CLAUSE_RE.match(ln.text)) and not equation_number(ln)

    def level4_size(ln: Line) -> bool:
        """A bold heading-font line smaller than the numbered level-3 headings: level 4 by size (H13a)."""
        l3 = b.level3_size()
        return l3 is not None and ln.is_bold and heading_font(ln) and ln.size < l3 - 0.4

    def small_heading(ln: Line) -> bool:
        """A numbered heading set bold in the heading font at body size (H7): taken only when its number
        is the next free child of the current clause or of one of its parents."""
        m = CLAUSE_RE.match(ln.text)
        if not (m and ln.is_bold and body_font and not ln.font.startswith(body_font)
                and abs(ln.size - body_size) < 0.9 and "." in m.group(1) and b.clause):
            return False
        parent, num = m.group(1).rsplit(".", 1)
        return (b.clause == parent or b.clause.startswith(parent + ".")) and int(num) == b.children[parent] + 1

    def style(ln: Line) -> tuple:
        return ln.font, round(ln.size * 2) / 2, ln.is_bold

    def continues(j: int, first: Line) -> bool:
        """lines[j] is a wrapped continuation of the heading that starts with `first`."""
        ln = lines[j]
        same = ln.font == first.font and (heading_font(ln) or (ln.is_bold and not ln.font.startswith(body_font)
                                                               and not ITEM_RE.match(ln.text)))
        return (is_heading(ln) or same) and ln.page == first.page \
            and abs(ln.size - first.size) < 0.6 and not CLAUSE_RE.match(ln.text) and not ANNEX_RE.match(ln.text) \
            and ln.top - lines[j - 1].bottom < 40

    def unnumbered_heading(k: int) -> tuple[str, int] | None:
        """Heading whose number is not in the text layer (H1): a heading-font line without a number,
        followed (machine IDs aside) by a letter list that restarts at 'a.'. Returns (title, next index)."""
        ln = lines[k]
        t = ln.text
        if not (heading_font(ln) or is_heading(ln)) or CLAUSE_RE.match(t) or CHAPTER_ONLY_RE.match(t) \
                or ANNEX_RE.match(t) or ANNEX_CLAUSE_RE.match(t) or DRD_RE.match(t) or ITEM_RE.match(t) \
                or NOTE_RE.match(t) or MACHINE_ID_RE.match(t) or t.lower().startswith("bibliography"):
            return None
        parts, j = [t], k + 1
        while j < n and lines[j].text and continues(j, ln) and not ITEM_RE.match(lines[j].text):
            parts.append(lines[j].text)
            j += 1
        nxt = j
        while nxt < n and (not lines[nxt].text or MACHINE_ID_RE.match(lines[nxt].text)):
            nxt += 1
        item = ITEM_RE.match(lines[nxt].text) if nxt < n else None
        if level4_size(ln):  # prose, a NOTE or a list may follow; the heading takes its number anyway
            return " ".join(parts), j
        if item and item.group(1) == "a" and (not item_x or abs(round(lines[nxt].x0) - item_x) <= 10):
            return " ".join(parts), j
        return None

    # a handbook without any chapter >= 4 (a glossary, E-HB-32-20 Part 8A): chapters 1 onwards are the body (H8)
    min_chapter = 4
    if handbook:
        def body_start(ln: Line) -> bool:
            m = CLAUSE_RE.match(ln.text) or CHAPTER_ONLY_RE.match(ln.text)
            return bool(ANNEX_RE.match(ln.text) or (m and int(m.group(1).split(".")[0]) >= 4))

        if not any(is_heading(ln) and body_start(ln) for ln in lines):
            min_chapter = 1

    active = False
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        text = ln.text
        if not text:
            i += 1
            continue
        if active:
            counts["body"] += len(text.split())

        cap = CAPTION_RE.match(text)
        if cap or i in table_lines:
            i += 1
            if not active:
                continue
            flush()
            b.finish()
            if (cap and cap.group(1) == "Table") or i - 1 in table_lines:
                tid = table_lines.get(i - 1) or f"Table {cap.group(2)}"
                b.table_info[tid] = (b.clause, b.pending_mid)
            b.pending_mid = ""
            while (i < n and is_heading(lines[i]) and lines[i].page == ln.page and not CLAUSE_RE.match(lines[i].text)
                   and not CAPTION_RE.match(lines[i].text) and i not in table_lines):
                i += 1  # wrapped caption line (not the next table's caption: two tables can follow each other)
            continue

        if active and b.numbered and (u := unnumbered_heading(i)):
            flush()
            b.infer_heading(u[0], style(ln), 4 if level4_size(ln) else None)
            i = u[1]
            continue

        if is_heading(ln) or (active and small_heading(ln)):
            flush()
            # merge wrapped headings and a chapter number printed on its own line
            parts = [text]
            j = i + 1
            while j < n and continues(j, ln):
                parts.append(lines[j].text)
                j += 1
            head = " ".join(parts)
            i = j
            m = CLAUSE_RE.match(head)
            a = ANNEX_RE.match(head)
            ac = ANNEX_CLAUSE_RE.match(head)
            if head.lower().startswith("bibliography"):
                b.finish()
                active = False
            elif a:
                active = True
                b.finish()  # close the last record under the previous informative/normative flag
                b.informative = a.group(2).lower() == "informative"
                b.heading(f"Annex {a.group(1)}", f"({a.group(2).lower()}) {a.group(3)}".strip(), 1)
                b.clause = a.group(1)
                b.numbered = ""  # no inferred numbers until the annex has a numbered clause
            elif m and "...." not in head:
                clause = m.group(1)
                chapter = int(clause.split(".")[0])
                if chapter >= min_chapter:
                    active = True
                    b.finish()
                    b.informative = False
                elif "." not in clause:
                    active = False
                if active:
                    b.heading(clause, m.group(2), clause.count(".") + 1, style(ln))
                    b.base_clause = clause
                    if "." not in clause:
                        b.glossary = handbook and "glossary" in m.group(2).lower()
            elif ac and active:
                b.heading(ac.group(1), ac.group(2), ac.group(1).count(".") + 1, style(ln))
                b.base_clause = ac.group(1)
            elif DRD_RE.match(head) and active:
                d = DRD_RE.match(head)
                base = b.base_clause or b.clause
                b.heading(f"{base}<{d.group(1)}>", d.group(2) or "", len(base.split(".")) + 1 + d.group(1).count("."))
            elif b.glossary and active:
                b.finish()  # letter-group heading ('A', 'B', ...): not a clause
            continue

        i += 1
        if not active:
            continue

        mid = MACHINE_ID_RE.match(text)
        if mid:
            flush()
            b.finish()
            b.pending_mid = text
            continue

        item = ITEM_RE.match(text)
        if item and (not item_x or abs(round(ln.x0) - item_x) <= 10):
            flush()
            b.start(item.group(1), item.group(2), ln.page)
            continue

        if ln.size < body_size - 1.5 or (body_font and not ln.font.startswith(body_font) and not LIST_RE.match(text)
                                         and not NOTE_RE.match(text) and ln.size != body_size):
            continue  # figure text drawn in another font/size
        req = b.current
        if b.glossary and active:
            # glossary entry (E-HB-32-20 Part 8A): an upper-case term line at the margin, its definition indented
            # below it (numbered senses and notes included)
            nxt = next((x for x in lines[i:i + 3] if x.text), None)
            letters = [c for c in text if c.isalpha()]
            if len(letters) >= 2 and sum(c.isupper() for c in letters) >= 0.8 * len(letters) \
                    and nxt is not None and nxt.x0 > ln.x0 + 5:
                b.start_term(text, "", ln.page)
                b.last = ln
                continue
            if req is not None and "glossary term" in req.flags:
                last = b.last
                para = last is not None and (ln.page != last.page or ln.top - last.bottom > 0.6 * ln.size)
                req.text = text if not req.text else f"{req.text}\n{text}" if para else _join(req.text, text)
                b.last = ln
                continue
        if b.handbook and (req is None or (req is b.section and not b.in_note and not NOTE_RE.match(text))):
            # handbook prose: the section's own guidance record, paragraphs on separate lines
            if req is None:
                b.start_section(text, ln.page)
            else:
                last = b.last
                new = ln.page == 0 or (last is not None and last.page == ln.page and ln.top - last.bottom > 0.6 * ln.size)
                req.text = f"{req.text}\n{text}" if new or _is_list(text, req.text) else _join(req.text, text)
            b.last = ln
            continue
        if req is None:  # descriptive clause text: an unparsed paragraph (H6)
            last = frag[-1] if frag else None
            # a new paragraph after a vertical gap; Word lines (page 0) are paragraphs already
            if last is not None and (ln.page == 0 or (last.page == ln.page and ln.top - last.bottom > 0.6 * ln.size)):
                flush()
            if not frag:
                frag_clause = b.clause
            frag.append(ln)
            continue

        note = NOTE_RE.match(text)
        if note:
            req.notes.append(note.group(2) or "")
            b.in_note = True
            b.note_x = ln.x0
            continue
        if b.in_note and (ln.x0 >= b.note_x - 3 or not item_x):
            sep = "\n" if _is_list(text, req.notes[-1]) else " "
            req.notes[-1] = (req.notes[-1] + sep + text).strip() if sep == "\n" else _join(req.notes[-1], text)
            continue
        b.in_note = False
        if _is_list(text, req.text):
            req.text = f"{req.text}\n{text}"
        else:
            req.text = _join(req.text, text)

    flush()
    b.finish()
    if stats is not None:
        stats.update(unparsed=unparsed, unparsed_words=counts["unparsed"], body_words=counts["body"])
    return b.reqs, b.table_info


def attach_tables(tables: list[Table], info: dict[str, tuple[str, str]]) -> None:
    for t in tables:
        clause, mid = info.get(t.table_id, ("", ""))
        t.clause = t.clause or clause
        t.machine_id = t.machine_id or mid


# --------------------------------------------------------------------------- Word


def word_lines(paragraphs: list[str]) -> list[Line]:
    """Turn LibreOffice-rendered paragraphs into pseudo layout lines for parse_ecss_lines.

    Indentation (leading spaces) stands in for x position; headings are recognised by
    their numbering and get a larger 'size' so the same parser handles both sources.
    """
    out: list[Line] = []
    for raw in paragraphs:
        expanded = raw.replace("\t", " ")
        text = " ".join(expanded.split())
        if not text:
            continue
        indent = len(expanded) - len(expanded.lstrip(" "))
        head = (
            (CLAUSE_RE.match(text) and not ITEM_RE.match(text) and len(text) < 160 and not text.endswith((".", ";", ":"))
             and indent == 0)
            or CHAPTER_ONLY_RE.match(text)
            or ANNEX_RE.match(text)
            or (ANNEX_CLAUSE_RE.match(text) and indent == 0 and len(text) < 160)
            or text.lower() == "bibliography"
        )
        out.append(Line(text=text, page=0, top=0, bottom=0, x0=float(indent * 4), size=14.0 if head else 10.0,
                        bold=1.0 if head else 0.0, italic=0.0, font="word"))
    # a chapter number on its own line is followed by its title: mark the title as heading too
    for k in range(len(out) - 1):
        if CHAPTER_ONLY_RE.match(out[k].text) and out[k].size > 10:
            out[k + 1].size, out[k + 1].bold = 14.0, 1.0
    return out
