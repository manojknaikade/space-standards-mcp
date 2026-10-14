"""Check an answer's citations and numbers against the loaded standards (answer eval, Phase 2).

Deterministic, no LLM: used by eval/run_answer_eval.py and, in Phase 3, by the agent to verify its own
citations before answering.

- **Citations**: requirement IDs (ECSS clause + letter "4.3.1a" / "4.3.1(a)", DRD "A.2.1<5.2>a", NASA-style
  tags with the prefixes the loaded documents use, e.g. "FSR 24", "FCR 11 / 7.2.8.c"), NASA guidance records
  ("4.1.1 guidance 3") and "Table n(-m)" references. Each is attributed to the nearest standard named before it
  in the answer; if that document lacks it, to the one loaded document that has it. An ID that exists in no
  loaded document is *invented*. An ID attached to a standard that is not loaded ("ECSS-Q-ST-70-71 4.3.10c",
  "Table 9-1 of ECSS-Q-ST-70-15") is *external*: it cannot be checked, so it is neither resolved nor invented.
- **Numbers**: every number in the answer (outside IDs, standard names and clause references) must appear
  in the question or in the text, notes or tables of a requirement or table the answer cites, or of the
  `extra_records` given (e.g. the records the client actually retrieved). Others are *ungrounded*.
  A number found *only* in tables of a document below `verified` (tier "checked" or "unchecked") is grounded
  only when the answer repeats the flag the tools put on those tables: "check against the source"
  (case-insensitive) or the table's page ("p. N", "page N", "pages N and M") in the number's own sentence, or in
  a flag-only sentence directly after it on the same line (no answer numbers of its own besides the page).
  Sentences end at `.` or `;` plus whitespace, never inside parentheses or brackets; a markdown table row is one
  sentence. A line ending in ":" that carries the flag, directly before a markdown table (blank lines allowed),
  flags the numbers in that table's rows. The flag elsewhere in the line or paragraph does not count. Otherwise the number is *ungrounded*
  and also listed in `unflagged` (a subset of `ungrounded`, so existing consumers still see it), with the
  document, table and page it comes from in `unflagged_sources`.
  Numbers also found in a record's text, in a verified table or in the question are unaffected.
- **Declines**: whether the answer says the loaded standards do not cover the question.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .index import CHECK_FLAG, HYPHENS_RE, STD_ID_RE, StandardsIndex, _norm_doc, _norm_table, std_name
from .models import Requirement, Table

ECSS_ID_RE = re.compile(r"(?<![\w.<])((?:[A-Z]\.)?\d+(?:\.\d+)+(?:<[\d.]+>)?)(?:\(([a-z])\)|([a-z]))(?![\w])")
GUIDANCE_RE = re.compile(r"(?<![\w.<])(\d+(?:\.\d+)*) (guidance|req) (\d+)\b")  # NASA '4.1 guidance 2', '4.4 req 1'
NASA_ITEM_RE = re.compile(r"(?<![\w.<])(\d+(?:\.\d+)*)\((\d{1,2})\)")  # tagless NASA numbered item, '4.3(1)'

TABLE_RE = re.compile(r"\bTable\s+(\d+(?:-\d+)?)\b", re.I)
NUMBER_RE = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?(?![\w]|[.,]\d)")
# clause references without a letter ('section 4.6', 'clause 8.2.3', '7.2.1'), revisions, list markers
# ... and the further items of a list or range ('clauses 5.4 to 5.7 and 5.8')
CLAUSE_RE = re.compile(r"\b(?:sections?|clauses?|§|paragraphs?|para\.?|annex)\s*,?\s*[A-Z]?\d+(?:\.\d+)*\b"
                       r"(?:\s*(?:,|-|–|to|and|or)\s*[A-Z]?\d+(?:\.\d+)+\b)*|\b\d+(?:\.\d+){2,}\b", re.I)
# an ID belongs to a standard that is not loaded when it follows that standard's name closely (same sentence) or
# is followed by "of/from/in <standard>"
ATTACH_GAP = 60
SENTENCE_BREAK_RE = re.compile(r"[.;]\s|\n")
# "Table 9-1 of X", "Table 9-1 values in X"
ATTACH_AFTER_RE = re.compile(r"\s*,?\s*(?:\w+\s+){0,2}?(?:of|from|in|per)\s+(?:the\s+)?", re.I)
# not values (eval scripted run 1): table ranges ("Tables 1-7", "Tables 4-3 to 4-6"), clause numbers in brackets
# ("(4.4)", "<5.3>"), shorthand standard names after the full one ("32-08C, 32C", "-32-01")
REFNOISE_RE = re.compile(r"\bTables\s+\d+(?:-\d+)?\s*(?:-|to|and|,)\s*\d+(?:-\d+)?"
                         r"|\(\d+(?:\.\d+)+\)|<\d+(?:\.\d+)*>|\b\d{2}(?:-\d{2})?[A-D]\b|(?<![\w-])-\d{2}-\d{2}\b", re.I)
# page references ("page 12", "p. 12", "pp. 12-13") are locations, not values
_PAGE_ITEM = r"\d+(?![.,]\d)(?:\s*-\s*\d+)?"
PAGE_RE = re.compile(rf"\b(?:pp?\.|pages?)\s*{_PAGE_ITEM}(?:\s*(?:,|and|&)\s*{_PAGE_ITEM})*", re.I)
TAG_RANGE_RE = re.compile(r"\s*(?:-|to|and|&)\s*(\d+)(?![\w.]*\d)", re.I)
# NASA guidance written with the clause in front: '4.4 (guidance 1, not a requirement)', '4.4 (req 2)'
GUIDANCE_PAREN_RE = re.compile(r"(?<![\w.<])\d+(?:\.\d+)*\s*\((?:guidance|req)\s*\d+", re.I)
# a clause number right after a standard's name: 'NASA-HDBK-7005, 4.6:', 'ECSS-E-HB-32-23A Rev.1, 12.2'
CLAUSE_AFTER_NAME_RE = re.compile(
    r"(?:[\s,]*(?:Rev\.?|Corr\.?|Issue|Change)\s*\d+)*\s*[,:]?\s*(\d+(?:\.\d+)+)(?![\w]|[.,]\d)", re.I)
# a paragraph number right after a document name, as NASA documents without requirement tags are cited:
# 'NASA-STD-7003A, 4.3.1.1', 'NASA-STD-7003A clause 4.3.1.1(2)', 'DOC para. 4.3.1.1'
PARA_AFTER_NAME_RE = re.compile(
    r"\s*,?\s*(?:(?:clauses?|sections?|§|paragraphs?|para\.?)\s*,?\s*)?(\d+(?:\.\d+)+)(?:\((\d{1,2})\))?(?![\w]|[.,]\d)", re.I)
# other documents' numbers: NASA-SP-8007, ANSI/AIAA S-081-2000, MIL-STD-1530
DOCREF_RE = re.compile(r"\b[A-Z][A-Z0-9/]*(?:-[A-Z0-9/]+)*-[A-Z]?\d[\w.-]*")
NOISE_RE = re.compile(r"\bRev\.?\s*\d+|\bChange\s+\d+|\bIssue\s+\d+|^\s*(?:#+\s*|\*\*)?\d+[.)]\s|\(\d+\)|\b\d{4}-\d{2}-\d{2}\b",
                      re.I | re.M)
# a launch-vehicle / spacecraft name with its number or numeral: 'Ariane 5', 'Atlas V', 'Long March 3B' (not answer values)
VEHICLE_RE = re.compile(
    r"\b(?:Ariane[\s-]?[3-6]|Atlas[\s-]?(?:III|II|IV|V|5)|Delta[\s-]?(?:IV|II|4)|Titan[\s-]?(?:IV|III|4)"
    r"|Saturn[\s-]?(?:V|IB|1B|5)|Soyuz[\s-]?2|Long[\s-]March[\s-]?\d+[A-Z]?|CZ-\d+[A-Z]?|H-?IIA|H-?IIB|H3"
    r"|GSLV[\s-]?Mk[\s-]?(?:III|II|3|2)|Antares[\s-]?\d+|SLS[\s-]Block[\s-]?1[AB]?|Falcon[\s-]?9)\b", re.I)
WORDS = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
         "nine": "9", "ten": "10", "hundred": "100", "thousand": "1000"}
DECLINE_RE = re.compile(
    r"(?:\bnot|n['’]t) (?:\w+ ){0,2}(?:covered|addressed|specified|included|loaded|available|given|defined|stated|found)"
    r"|do(?:es)?(?: not|n['’]t) (?:\w+ ){0,2}(?:cover|specify|give|contain|define|address|provide|state|include)"
    r"|(?:\bnot|n['’]t) (?:one of|among) the loaded"
    r"|(?:no|none of the) (?:\w+ ){0,4}(?:requirement|value|limit|level|criteri\w+|number|factor)s? (?:\w+ ){0,3}"
    r"(?:in|from) the loaded"
    r"|outside (?:the scope of )?the loaded",
    re.I,
)


@dataclass
class Citation:
    raw: str  # as written in the answer
    kind: str  # "requirement" | "table"
    ref: str  # normalised ID: "4.3.1a", "FSR 24", "Table 4-3"
    doc_id: str | None = None  # resolved loaded document (None: invented, or ambiguous)
    status: str = "ok"  # ok | invented | ambiguous | external

    @property
    def key(self) -> str | None:
        return f"{self.doc_id}|{self.ref}" if self.doc_id else None


@dataclass
class AnswerCheck:
    citations: list[Citation] = field(default_factory=list)
    numbers: list[str] = field(default_factory=list)
    ungrounded: list[str] = field(default_factory=list)
    unflagged: list[str] = field(default_factory=list)  # subset of ungrounded: table values without the flag
    unflagged_sources: dict[str, list[str]] = field(default_factory=dict)  # unflagged number -> "DOC Table n, page p"
    declines: bool = False

    @property
    def cited_keys(self) -> set[str]:
        return {c.key for c in self.citations if c.key}

    @property
    def invented(self) -> list[str]:
        return [c.raw for c in self.citations if c.status == "invented"]

    def to_dict(self) -> dict:
        return {
            "cited": sorted(self.cited_keys),
            "invented": self.invented,
            "ambiguous": [c.raw for c in self.citations if c.status == "ambiguous"],
            "external": [c.raw for c in self.citations if c.status == "external"],
            "numbers": self.numbers,
            "ungrounded": self.ungrounded,
            "unflagged": self.unflagged,
            "unflagged_sources": self.unflagged_sources,
            "declines": self.declines,
        }


def _num(s: str) -> str:
    """'1,25' / '1.250' / '1.0' / '05' -> '1.25' / '1.25' / '1' / '5'."""
    s = s.replace(",", ".")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    whole, _, frac = s.partition(".")
    whole = whole.lstrip("0") or "0"
    return f"{whole}.{frac}" if frac else whole


def _numbers(text: str) -> set[str]:
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)
    found = {_num(m) for m in re.findall(r"\d+(?:\.\d+)?", text)}
    found |= {WORDS[w.lower()] for w in re.findall(r"\b(?:" + "|".join(WORDS) + r")\b", text, re.I)}
    return found


def _record_text(r: Requirement) -> str:
    return " ".join([r.text, *r.notes])


def _table_text(t: Table) -> str:
    parts = [t.caption, *t.label_columns, *t.value_columns, *t.footnotes.values(), *t.units.values()]
    for row in t.rows:
        parts += [*row.labels.values(), *(c.text for c in row.cells.values())]
    return " ".join(parts)


class CitationChecker:
    def __init__(self, index: StandardsIndex):
        self.index = index
        # NASA-style tag prefixes in use and their separator: {"FSR": " ", "SWE": "-"}
        self._tag_sep = {m.group(1): m.group(2) for d in index.documents for r in d.requirements
                         if (m := re.match(r"([A-Z][A-Z0-9]{1,9})([ -])\d", r.req_id))}
        prefixes = self._tag_sep
        # '4.3(1)' is an ID only where a loaded document uses that form (elsewhere it may be an equation)
        self._nasa_items = any(NASA_ITEM_RE.fullmatch(r.req_id) for d in index.documents for r in d.requirements)
        self._tag_re = (re.compile(r"\b(" + "|".join(sorted(prefixes, key=len, reverse=True)) + r")[ -](\d+)"
                                   r"(?:\s*/\s*(\d+(?:\.\d+)*(?:\.[a-z])?))?(?![\w.]*\d)")
                        if prefixes else None)
        # (normalised doc ID, where an answer names it); parts, volumes and annexes as in index.doc_pattern
        self._doc_patterns = index._doc_patterns

    # -- citations -------------------------------------------------------------------------------
    def _mentions(self, text: str) -> list[tuple[int, int, tuple[str, ...] | None]]:
        """(start, end, normalised doc IDs, or None for a standard that is not loaded). Several IDs when
        the name stands for several loaded documents: 'ECSS-E-HB-32-20' for its loaded parts."""
        up = HYPHENS_RE.sub("-", text.upper())
        spans: dict[tuple[int, int], list[str]] = {}
        for d, pat in self._doc_patterns:
            for m in pat.finditer(up):
                spans.setdefault(m.span(), []).append(d)
        out: list[tuple[int, int, tuple[str, ...] | None]] = [(s, e, tuple(ds)) for (s, e), ds in spans.items()]
        for m in STD_ID_RE.finditer(up):
            inside_loaded = any(s < m.end() and m.start() < e for s, e in spans)  # 'NPR 1' in 'X NPR 1'
            if not inside_loaded and not self.index._match_doc(std_name(m)):
                out.append((m.start(), m.end(), None))
        return sorted(out, key=lambda x: x[:2])

    def _resolve(self, ref: str, before: tuple[str, ...] | None, has) -> tuple[str | None, str]:
        named = [d for d in before or () if has(d, ref)]
        if len(named) == 1:
            return named[0], "ok"
        owners = [_norm_doc(d.doc_id) for d in self.index.documents if has(_norm_doc(d.doc_id), ref)]
        if len(owners) == 1:
            return owners[0], "ok"
        return None, "ambiguous" if owners else "invented"

    def _has_req(self, doc: str, ref: str) -> bool:
        return self.index.get(doc, ref) is not None

    def _anywhere(self, ref: str) -> bool:
        return any(self._has_req(d.doc_id, ref) for d in self.index.documents)

    def _has_table(self, doc: str, ref: str) -> bool:
        return self.index.get_table(doc, ref) is not None

    def find_citations(self, text: str, default_doc: str | None = None) -> list[Citation]:
        mentions = self._mentions(text)

        def doc_before(pos: int) -> tuple[str, ...] | None:
            prev = [d for s, _, d in mentions if s < pos]
            return prev[-1] if prev else (default_doc,) if default_doc else None

        def external(start: int, end: int) -> bool:
            """The ID is attached to a standard that is not loaded."""
            prev = [(e, d) for s, e, d in mentions if e <= start]
            if prev and prev[-1][1] is None:
                gap = text[prev[-1][0]:start]
                if len(gap) <= ATTACH_GAP and not SENTENCE_BREAK_RE.search(gap):
                    return True
            m = ATTACH_AFTER_RE.match(text, end)
            return bool(m) and any(s == m.end() and d is None for s, _, d in mentions)

        found: list[tuple[int, int, str, str]] = []  # start, end, kind, ref
        if self._tag_re:
            for m in self._tag_re.finditer(text):
                tag = f"{m.group(1)}{self._tag_sep[m.group(1)]}"
                ref = f"{tag}{m.group(2)}" + (f" / {m.group(3)}" if m.group(3) else "")
                # 'PVTR 43/44' is shorthand for two tags, not a 'FCR 8 / 6.2.1'-style ID, when no record has
                # that ID and both tags exist (r12 w1-002: the gate declined a correct answer)
                if (m.group(3) and m.group(3).isdigit() and not self._anywhere(ref)
                        and self._anywhere(f"{tag}{m.group(2)}") and self._anywhere(f"{tag}{m.group(3)}")):
                    found.append((m.start(), m.start(3) - 1, "requirement", f"{tag}{m.group(2)}"))
                    found.append((m.start(3), m.end(), "requirement", f"{tag}{m.group(3)}"))
                    continue
                found.append((m.start(), m.end(), "requirement", ref))
        for m in GUIDANCE_RE.finditer(text):
            found.append((m.start(), m.end(), "requirement", f"{m.group(1)} {m.group(2)} {m.group(3)}"))
        if self._nasa_items:
            for m in NASA_ITEM_RE.finditer(text):
                found.append((m.start(), m.end(), "requirement", f"{m.group(1)}({m.group(2)})"))
        # tagless NASA records are cited by paragraph number; a number that is no record of the named
        # document stays a plain section reference (not reported as invented)
        for _, mend, docs in mentions:
            if docs is None or not (m := PARA_AFTER_NAME_RE.match(text, mend)):
                continue
            refs = [f"{m.group(1)}({m.group(2)})"] if m.group(2) else []
            for ref in [*refs, m.group(1)]:
                if any(self._has_req(d, ref) for d in docs):
                    found.append((m.start(1), m.end(2) + 1 if m.group(2) and ref != m.group(1) else m.end(1),
                                  "requirement", ref))
                    break
        taken = [(s, e) for s, e, *_ in found]
        for m in ECSS_ID_RE.finditer(text):
            if any(s <= m.start() < e for s, e in taken):
                continue
            found.append((m.start(), m.end(), "requirement", m.group(1) + (m.group(2) or m.group(3))))
        for m in TABLE_RE.finditer(text):
            found.append((m.start(), m.end(), "table", f"Table {m.group(1)}"))

        out, seen = [], set()
        for start, end, kind, ref in sorted(found):
            if external(start, end):
                doc, status = None, "external"
            else:
                has = self._has_req if kind == "requirement" else self._has_table
                doc, status = self._resolve(ref, doc_before(start), has)
            if (doc, ref, status) in seen:
                continue
            seen.add((doc, ref, status))
            if doc:
                obj = self.index.get(doc, ref) if kind == "requirement" else self.index.get_table(doc, ref)
                ref = obj.req_id if kind == "requirement" else obj.table_id
                doc = obj.doc_id
            out.append(Citation(text[start:end], kind, ref, doc, status))
        return out

    # -- numbers ---------------------------------------------------------------------------------
    def _grounding(self, citations: list[Citation], extra: list[str],
                   extra_tables: list[Table] = ()) -> tuple[set[str], list[tuple[set[str], int | None, str]]]:
        """(numbers grounded outright, [(numbers, page, "DOC Table n") of each cited table below `verified`])."""
        texts = list(extra)
        flagged: list[tuple[set[str], int | None, str]] = []

        def add_table(t: Table) -> None:
            if self.index.tier_of(t.doc_id, t.issue) == "verified":
                texts.append(_table_text(t))
            else:
                flagged.append((_numbers(_table_text(t)), t.page, f"{t.doc_id} {t.table_id}"))

        for t in extra_tables:
            add_table(t)
        for c in citations:
            if not c.doc_id:
                continue
            if c.kind == "table":
                add_table(self.index.get_table(c.doc_id, c.ref))
                continue
            r = self.index.get(c.doc_id, c.ref)
            texts.append(_record_text(r))
            for t in (self.index.get_table(r.doc_id, x) for x in r.tables):
                if t:
                    add_table(t)
        return _numbers(" ".join(texts)), flagged

    @staticmethod
    def _segments(answer: str) -> list[list[str]]:
        """Sentences per line: split at `.` / `;` plus whitespace, not inside () or [], not after "p"/"pp";
        a markdown table row is one segment."""
        out = []
        for line in answer.split("\n"):
            if line.lstrip().startswith("|"):
                out.append([line])
                continue
            segs, depth, start = [], 0, 0
            for i, ch in enumerate(line):
                if ch in "([":
                    depth += 1
                elif ch in ")]":
                    depth = max(0, depth - 1)
                elif ch in ".;" and depth == 0 and line[i + 1:i + 2].isspace():
                    if ch == "." and re.search(r"\bpp?$", line[start:i], re.I):
                        continue
                    segs.append(line[start:i])
                    start = i + 1
            segs.append(line[start:])
            out.append(segs)
        return out

    @staticmethod
    def _page_refs(seg: str) -> set[int]:
        return {int(n) for m in PAGE_RE.finditer(seg) for n in re.findall(r"\d+", m.group())}

    def _has_flag(self, seg: str, pages: set[int | None]) -> bool:
        return CHECK_FLAG in seg.lower() or bool(self._page_refs(seg) & {p for p in pages if p})

    def _intro_flag(self, lines: list[str], li: int, pages: set[int | None]) -> bool:
        """Line `li` is a row of a markdown table whose introducing line (blank lines allowed in between) ends
        with ":" and carries the flag; list marker and bold are ignored."""
        i = li
        while i >= 0 and lines[i].lstrip().startswith("|"):
            i -= 1
        while i >= 0 and not lines[i].strip():
            i -= 1
        if i < 0 or i == li:
            return False
        intro = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", lines[i]).replace("*", "").rstrip()
        return intro.endswith(":") and self._has_flag(intro, pages)

    def _repeats_flag(self, answer: str, number: str, pages: set[int | None]) -> bool:
        """The number's sentence says "check against the source" or cites the page of a table that holds it,
        or the next sentence on the same line does and has no answer numbers of its own."""
        text = HYPHENS_RE.sub("-", answer)
        lines = text.split("\n")
        for li, segs in enumerate(self._segments(text)):
            if (lines[li].lstrip().startswith("|") and number in self.answer_numbers(lines[li])
                    and self._intro_flag(lines, li, pages)):
                return True
            for i, seg in enumerate(segs):
                if number not in self.answer_numbers(seg):
                    continue
                if self._has_flag(seg, pages):
                    return True
                nxt = segs[i + 1] if i + 1 < len(segs) else None
                if nxt is not None and self._has_flag(nxt, pages) and not self.answer_numbers(nxt):
                    return True
        return False

    def answer_numbers(self, text: str) -> list[str]:
        """Numbers stated in the answer, without those inside IDs, standard names and clause references."""
        text = HYPHENS_RE.sub("-", text)
        up = text.upper()  # same length: spans found on it apply to text
        spans = [m.span() for m in STD_ID_RE.finditer(up)]
        spans += [m.span() for _, pat in self._doc_patterns for m in pat.finditer(up)]
        for _, e in list(spans):  # clause numbers right after a standard's name
            if m := CLAUSE_AFTER_NAME_RE.match(text, e):
                spans.append(m.span(1))
        for m in DOCREF_RE.finditer(text):
            if c := CLAUSE_AFTER_NAME_RE.match(text, m.end()):
                spans.append(c.span(1))
        if self._tag_re:  # second number of a tag range: 'FSR 33-36', 'PVTR 3 to 5'
            for m in self._tag_re.finditer(text):
                if r := TAG_RANGE_RE.match(text, m.end()):
                    spans.append(r.span(1))
        for pat in (DOCREF_RE, CLAUSE_RE, PAGE_RE, NOISE_RE, VEHICLE_RE, REFNOISE_RE, GUIDANCE_RE, GUIDANCE_PAREN_RE, ECSS_ID_RE,
                    TABLE_RE,
                    *([self._tag_re] if self._tag_re else []), *([NASA_ITEM_RE] if self._nasa_items else [])):
            spans += [m.span() for m in pat.finditer(text)]
        chars = list(text)
        for a, b in spans:
            chars[a:b] = " " * (b - a)
        masked = re.sub(r"(\d),(\d)", r"\1.\2", "".join(chars))
        return list(dict.fromkeys(_num(m) for m in NUMBER_RE.findall(masked)))

    def check(self, answer: str, question: str = "", extra_records: list[str] | None = None) -> AnswerCheck:
        """extra_records: 'doc|id' keys (requirements or tables) whose text also grounds numbers."""
        detected = self.index.detect_documents(question) if question else []
        cits = self.find_citations(answer, detected[0] if len(detected) == 1 else None)
        extra_texts, extra_tables = [question], []
        for key in extra_records or []:
            doc, ref = key.split("|", 1)
            if (t := self.index.get_table(doc, ref)) and ref.lower().startswith("table"):
                extra_tables.append(t)
            elif r := self.index.get(doc, ref):
                extra_texts.append(_record_text(r))
        grounded, flagged = self._grounding(cits, extra_texts, extra_tables)
        nums = self.answer_numbers(answer)
        # a dotted number equal to the clause (or a parent clause) of a cited record is a reference, not a
        # value: 'Modal analysis (5.7)', 'the checks in 5.4 to 5.7' next to cited 5.7a (r12 hand-05)
        clauses = {_num(".".join(parts[:k])) for c in cits if c.kind == "requirement" and c.doc_id
                   and (r := self.index.get(c.doc_id, c.ref)) and r.clause
                   for parts in [r.clause.split(".")] for k in range(2, len(parts) + 1)}
        ungrounded, unflagged, sources = [], [], {}
        for n in nums:
            if n in grounded or n in clauses:
                continue
            pages = {p for numbers, p, _ in flagged if n in numbers}
            if not pages:
                ungrounded.append(n)
            elif not self._repeats_flag(answer, n, pages):
                ungrounded.append(n)
                unflagged.append(n)
                sources[n] = list(dict.fromkeys(f"{src}, page {p}" if p else src
                                                for numbers, p, src in flagged if n in numbers))
        return AnswerCheck(
            citations=cits,
            numbers=nums,
            ungrounded=ungrounded,
            unflagged=unflagged,
            unflagged_sources=sources,
            declines=bool(DECLINE_RE.search(answer)),
        )


def norm_key(key: str) -> str:
    """'ECSS-E-ST-32-10C|Table 4-3' -> comparable form (document and table IDs normalised)."""
    doc, ref = key.split("|", 1)
    ref = f"Table {_norm_table(ref)}" if ref.lower().startswith("table") else ref.strip().lower()
    return f"{_norm_doc(doc)}|{ref}"
