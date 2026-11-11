"""In-memory index: lookup by ID and keyword search.

Search is BM25 over requirement records and table rows (eval run 1 fixes, eval/RESULTS.md):
- documents named in the query ("NASA-STD-5001B", "ECSS-E-ST-32-01", or just "ECSS") restrict
  the search to those documents unless a doc_id is passed explicitly;
- BM25 length normalisation stops a few long records from winning every query;
- table rows (caption, column headers, row labels, cells, row footnotes) are indexed, and a row
  match is credited to the requirement(s) that point to the table, with the row attached.

Hybrid search (Phase 3, optional): with an embedder (spacestd.embeddings), records and table rows are also
ranked by cosine similarity to the query, and the two rankings are fused by reciprocal rank (RRF). BM25
still decides coverage: `elsewhere` and `compare_topic` coverage compare lexical scores, as calibrated on
the eval, so an embedding near-miss never turns "not covered" into "covered". An optional cross-encoder
reranker then reorders the top RERANK_POOL hits (same rule: ranking only, never coverage).
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from itertools import zip_longest

from .catalogue import VERIFIED, Catalogue, classify
from .editions import issue_differs, issue_words
from .models import Document, Requirement, Table, TableRow
from .parser import is_handbook

TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "be", "shall", "is", "on", "with", "by", "as", "that",
    "this", "what", "does", "do", "which", "how", "when", "can", "are", "it", "its", "under", "each", "there", "e-g",
}
HYPHENS_RE = re.compile(r"[‐‑‒–−]")
K1, B = 1.2, 0.5  # b < 0.75: long ECSS clauses (32-01 11.2.2.6a) were over-penalised (eval run 3)
# score multiplier per record kind: explanatory guidance should not outrank the requirement it
# explains (hand test F5: 5019A "7.3 guidance 10" above FCR 12 / 7.3.2.c)
# "table": synthetic owner of a table no record points to (cite the table); like guidance
# "definition": a term's definition should not outrank the requirement that uses the term
KIND_WEIGHT = {"guidance": 0.8, "deleted": 0.5, "table": 0.8, "definition": 0.8}
# handbook section records (A5) come on top of the guidance weight: a standard's requirement outranks a
# handbook section that matches the query as well
HANDBOOK_WEIGHT = 0.85
# a question that asks for a definition: definition records get this weight instead of KIND_WEIGHT's
DEFINITION_ASKED = 1.5
DEFINE_RE = re.compile(r"\bdefin(?:e[sd]?|ition|itions)\b|\bterminology\b|\bmeans? by\b|\bmeaning of\b|\bwhat (?:exactly )?is (?:a|an|the) ['\"‘“]", re.I)


def record_weight(req: Requirement) -> float:
    return KIND_WEIGHT.get(req.kind, 1.0) * (HANDBOOK_WEIGHT if is_handbook(req.doc_id) else 1.0)


# best named-document score below this fraction of the best score elsewhere (topic words only) -> also
# show the other documents' hits (hand test F6). On the 36 eval questions: 0.44 for the one question
# whose named standard lacks the topic; 0.69 for one that does (it gets three extra hits, harmlessly);
# >= 0.84 for all others.
WEAK_RATIO = 0.75
# hybrid search: reciprocal rank fusion constant, and how many dense hits enter the fusion
RRF_K = 60
DENSE_POOL = 50
# embedding share in the fusion: 2 was best on the real documents (eval/RESULTS.md, run 8)
DENSE_WEIGHT = 2.0
RERANK_POOL = 30
# records looked at when ranking whole documents on a topic (rank_documents)
DOC_POOL = 300
# compare_topic without doc_ids: above COMPARE_DOCS loaded documents, only the best COMPARE_PER_FAMILY per family
COMPARE_DOCS = 8
COMPARE_PER_FAMILY = 3
# records shown next to each hit: up to this many on either side within the same clause (6.3.3d -> 6.3.3c, 6.3.3e).
# A requirement is often split over sibling letters, and a sibling that shares no query word ranks far down
# (fs-027: 32-01 6.3.3c, no fragment release, at rank 36 although 6.3.3d is at rank 2)
NEIGHBOURS = 1
# part of a multi-part document after its number, as loaders.py writes it into the doc_id ("ECSS-E-HB-32-20
# Part 1A", "NASA-HDBK-5010 Vol 1", "NASA-STD-8719.24 Annex") and as people write it ("Part1A", "Volume 1",
# "Vol. 1"). Only NASA issues an annex as its own document; "ECSS-E-ST-32C Annex A" is inside the standard.
PART_SEP = r"[\s_-]*"
PART_PAT = r"PART[\s_-]*(?P<part>\d+)(?P<pissue>[A-Z])?|VOL(?:UME)?\.?[\s_-]*(?P<vol>\d+)"
ANNEX_PAT = r"ANNEX"
# standard IDs in a query (upper-cased, hyphens normalised), loaded or not, with their part / volume / annex
STD_ID_RE = re.compile(r"(?<![A-Z0-9-])(?P<std>ECSS-[A-Z]-(?:ST|HB|TM|AS)-\d{2}(?:-\d{2})?[A-Z]?"
                       r"|(?P<nasa>NASA-(?:STD|HDBK|SPEC)-\d{4,5}(?:\.\d+(?:-\d(?!\d))?)?[A-Z]?)"
                       r"|NPR ?\d{4}\.\d+[A-Z]?)(?![A-Z0-9]|[-.]\d)"
                       rf"(?:{PART_SEP}(?:{PART_PAT}|(?(nasa){ANNEX_PAT}|(?!)))(?![A-Z0-9]))?")
# designations of other bodies' standards, as a question may name them ("SMC-S-016", "MIL-STD-1540E",
# "ISO 24113", "DO-178C"): never held here, even when a loaded standard refers to them
EXTERNAL_STD_RE = re.compile(
    r"(?<![A-Z0-9-])(?:MIL-(?:STD|HDBK|DTL|PRF|SPEC)-\d+[A-Z]?|SMC-S-\d+|TOR-\d{4}\(\d+\)-\d+|ISO(?:/IEC)? ?\d{3,5}(?:-\d+)?"
    r"|IEC ?\d{4,5}(?:-\d+)*|AIAA ?S-\d+[A-Z]?(?:-\d{4})?|IEEE ?\d{3,5}|ASTM ?[A-Z]\d+|DO-(?:178|254|160)[A-G]?"
    r"|(?:JSC|MSFC|GSFC|KSC|JPL)-(?:STD|SPEC|HDBK|RQMT|D)-\d+[A-Z]?|JSC ?\d{5}|MISRA(?:[ -]C(?:\+\+)?)?(?:[: ]?\d{4})?"
    r"|ESCC ?\d{4,7}|CCSDS ?\d{3}\.\d-[A-Z]-\d|IPC-[A-Z]?-?\d+[A-Z]?|SAE ?A[SR]P?\d+[A-Z]?)(?![A-Z0-9])")
# words in capitals that are not designations of a subject
PLAIN_CAPS = {"ECSS", "NASA", "NPR", "ESA", "DC", "AC", "OK", "TBD", "TBC", "US", "EU", "PDR", "CDR", "QR", "AR", "SRR"}
DESIGNATION_RE = re.compile(r"(?<![\w-])(?:[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)*|\d+[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*|[A-Z]+\d+[A-Z0-9]*)(?![\w-])")
# an identifier printed at the start of a record's text: '[M&S 26] ...', 'Requirement 4.4-1: ...'
PRINTED_ID_RE = re.compile(r"\s*(?:\[([A-Z][A-Z0-9&]{1,9}[ -]\d+)\]|Requirement (\d+(?:\.\d+)*-\d+)\b)")
# the item part of an ID below a record: '5.2.2a', '12.3.5.c(3)', '4.3(1)', '5.5.1.a'
ITEM_SUFFIX_RE = re.compile(r"(?:\.?\(\d{1,2}\)|\.?[a-z])$")
# a doc_id with its part, normalised: 'ECSS-E-HB-32-20-PART-1A' -> base, part suffix
PART_ID_RE = re.compile(r"(.+?)-(PART-\d+[A-Z]?|VOL-\d+|ANNEX)$")
# a heading as parsed: '5.1 General', '4.3.2', 'A.2 Content' -> (number, title)
HEADING_RE = re.compile(r"((?:\d+|[A-Z](?=\.))(?:\.\d+)*)(?:\s+(.*))?$")


# nouns ending in -ing that are not inflections ('fairing' must not become 'fair')
NO_STEM = {"fairing", "bearing", "housing", "ceiling", "spring", "string", "during", "lining"}


def stem(word: str) -> str:
    """Light suffix stripping so inflections meet: 'testing'/'tested'/'tests' -> 'test',
    'welds' -> 'weld', 'requires'/'required' -> 'requir' (hand test F5: "proof test" vs
    "proof testing"). Words with digits or hyphens, and short words, are left alone."""
    if not word.isalpha() or len(word) <= 4:
        return word
    w = word
    if w.endswith("ies") and len(w) > 5:
        w = w[:-3] + "y"
    elif w.endswith("sses"):
        w = w[:-2]
    elif w.endswith("s") and not w.endswith(("ss", "us", "is")):
        w = w[:-1]
    if w in NO_STEM:
        return w
    for suffix in ("ing", "ed"):
        rest = w[: -len(suffix)]
        if w.endswith(suffix) and len(rest) >= 4 and re.search(r"[aeiouy]", rest):
            w = rest
            if len(w) > 3 and w[-1] == w[-2] and w[-1] not in "lsz":
                w = w[:-1]  # 'cutting' -> 'cut'
            break
    if w.endswith("e") and len(w) >= 5:
        w = w[:-1]
    return w


def tokenize(text: str) -> list[str]:
    """Stemmed words, keeping hyphenated compounds whole and adding their word parts ("payload-fairing"
    -> also "payload", "fairing"), so "non-discontinuity" still matches "discontinuity"."""
    out = []
    for t in TOKEN_RE.findall(HYPHENS_RE.sub("-", text.lower())):
        if t in STOPWORDS:
            continue
        out.append(stem(t))
        if "-" in t:
            out.extend(stem(p) for p in t.split("-") if len(p) >= 3 and p.isalpha() and p not in STOPWORDS)
    return out


def _norm_doc(doc_id: str) -> str:
    return re.sub(r"[\s_]+", "-", HYPHENS_RE.sub("-", doc_id.strip().upper()))


def _norm_table(table_id: str) -> str:
    """'Table 4-3', 'table 4‐3', '4-3' -> '4-3'."""
    t = re.sub(r"^\s*table\s*", "", table_id.strip(), flags=re.I)
    return HYPHENS_RE.sub("-", t).replace(" ", "").lower()


def _family(doc_id: str) -> str:
    d = _norm_doc(doc_id)
    return "ECSS" if d.startswith("ECSS") else "NASA" if d.startswith(("NASA", "NPR")) else ""


def std_name(m: re.Match) -> str:
    """A STD_ID_RE match in doc_id form: 'NASA-HDBK-5010 VOLUME 1' -> 'NASA-HDBK-5010 Vol 1'."""
    name = re.sub(r"\s+", " ", m["std"])
    if m["part"]:
        return f"{name} Part {m['part']}{m['pissue'] or ''}"
    if m["vol"]:
        return f"{name} Vol {m['vol']}"
    return f"{name} Annex" if m["nasa"] and m.group(0).endswith(ANNEX_PAT) else name


def doc_pattern(doc_id: str, bare: bool = True) -> re.Pattern:
    """Where a document is named in upper-cased text (hyphens normalised; same length as the original, so
    spans apply to it): the full ID or the ID without its issue letter, with '-', '_' or spaces between
    its parts, as a whole word. A part, volume or annex follows the number in any usual spelling
    ('Part1A', 'Part 1', 'Volume 1', 'Vol. 1'); with `bare` (the number alone is not a loaded document), the
    bare number names every part. 'X Part 3A' does not name 'X Part 1A', nor 'X' itself (nor does
    'NASA-STD-n Annex' name NASA-STD-n)."""
    d = _norm_doc(doc_id)
    m = PART_ID_RE.fullmatch(d)
    std, part = (m.group(1), m.group(2)) if m else (d, "")
    base = std[:-1] if re.search(r"\d[A-Z]$", std) else std
    pat = r"[-_\s]+".join(map(re.escape, base.split("-")))
    if std != base:
        pat += f"(?:{re.escape(std[len(base):])})?"
    other_part = r"PART[\s_-]*\d|VOL(?:UME)?\.?[\s_-]*\d"
    if std.startswith("NASA"):
        other_part += rf"|{ANNEX_PAT}(?![A-Z0-9])"
    no_part = rf"(?!{PART_SEP}(?:{other_part}))"
    if part and not bare:
        no_part = "(?!)"
    if part.startswith("PART"):
        num, issue = re.fullmatch(r"PART-(\d+)([A-Z]?)", part).groups()
        pat += rf"(?:{PART_SEP}PART[\s_-]*{num}(?:{issue})?|{no_part})"
    elif part.startswith("VOL"):
        pat += rf"(?:{PART_SEP}VOL(?:UME)?\.?[\s_-]*{part[4:]}|{no_part})"
    elif part:
        pat += rf"(?:{PART_SEP}{ANNEX_PAT}|{no_part})"
    else:
        pat += no_part
    return re.compile(rf"(?<![A-Z0-9]){pat}(?![A-Z0-9]|[-.]\d)")


@dataclass
class SearchHit:
    score: float
    requirement: Requirement
    table: Table | None = None  # set when the best match was a row of a table the requirement points to
    row: TableRow | None = None
    lexical: float = 0.0  # BM25 score (= score without an embedder); coverage decisions use this
    dense: float | None = None  # cosine similarity when hybrid search ranked the hit
    rerank: float | None = None  # cross-encoder score when a reranker reordered the hit

    def to_dict(self) -> dict:
        d = {"score": self.score, **self.requirement.to_dict()}
        if self.dense is not None:
            d["lexical_score"] = self.lexical
            d["dense_score"] = self.dense
        if self.rerank is not None:
            d["lexical_score"] = self.lexical
            d["rerank_score"] = self.rerank
        if self.table is not None and self.row is not None:
            d["matched_table_row"] = {"citation": self.table.citation, "table_id": self.table.table_id,
                                      "caption": self.table.caption, **self.row.to_dict()}
            if self.table.page:
                d["matched_table_row"]["page"] = self.table.page
        return d


def ISSUE_SPAN(after: str) -> int:
    """Length of the issue words at the start of `after` (what follows a document name)."""
    from .editions import ISSUE_WORD_RE

    pos = 0
    while m := ISSUE_WORD_RE.match(after, pos):
        pos = m.end()
    return pos


CHECK_FLAG = "check against the source"


def check_flag(page: int | None) -> str:
    """The flag on values from tables below `verified`; the citation gate looks for it in answers."""
    return f"{CHECK_FLAG}, page {page}" if page else CHECK_FLAG


def _row_text(t: Table, row: TableRow) -> str:
    marks = {m for c in row.cells.values() for m in c.footnotes}
    return " ".join([
        t.caption, *t.label_columns, *row.labels.values(), *t.value_columns,
        *(c.text + (" " + t.footnotes.get("shaded", "shaded") if c.shaded else "") for c in row.cells.values()),
        *(t.footnotes[m] for m in sorted(marks) if m in t.footnotes),
    ])


TAG_IN_ROW_RE = re.compile(r"\[([A-Z][A-Z0-9]{1,9}[ -]\d+)\]")


def _tagged_records(text: str, by_id: dict[str, Requirement]) -> list[Requirement]:
    """Records named by a bracketed tag in a table row ('[FCR 8]'): the record with exactly that ID, else the
    records of that tag ('FCR 8 / 6.2.1', ...). A table row naming one is a requirements-matrix copy."""
    out: list[Requirement] = []
    for tag in dict.fromkeys(TAG_IN_ROW_RE.findall(text)):
        exact = by_id.get(tag)
        out += [exact] if exact else [r for k, r in by_id.items() if k.startswith(tag + " /")]
    return list({id(r): r for r in out}.values())


def _req_text(req: Requirement) -> str:
    return " ".join([*req.heading_path, req.text, *req.notes])


class StandardsIndex:
    def __init__(self, documents: list[Document], embedder=None, dense_weight: float = DENSE_WEIGHT, reranker=None,
                 catalogue: Catalogue | None = None):
        """Optional (spacestd.embeddings): embedder -> hybrid search, dense_weight scales its RRF share;
        reranker -> the top RERANK_POOL hits are reordered by a cross-encoder.
        catalogue (spacestd.catalogue): every standard in the documents folder, for list_documents and to tell
        a named standard that is present but not loaded from one that is not in the folder."""
        self.documents = documents
        self.catalogue = catalogue
        self._by_key: dict[tuple[str, str], Requirement] = {}
        self._tables: dict[tuple[str, str], Table] = {}
        for doc in documents:
            for t in doc.tables:
                self._tables[(_norm_doc(t.doc_id), _norm_table(t.table_id))] = t
            for req in doc.requirements:
                self._by_key[(_norm_doc(req.doc_id), req.req_id.lower())] = req
        # a NASA record is also found by its clause ('4.1.2.2a' for FSR 13), when only one record has that clause
        clauses = Counter((_norm_doc(r.doc_id), r.clause.lower()) for d in documents for r in d.requirements if r.clause)
        for doc in documents:
            for req in doc.requirements:
                k = (_norm_doc(req.doc_id), req.clause.lower())
                if req.clause and clauses[k] == 1:
                    self._by_key.setdefault(k, req)
        # the identifier a document prints at the start of a requirement, when the parser kept the paragraph
        # number as its ID: '[M&S 26] ...' (a tag form the tag pattern does not know), 'Requirement 4.4-1: ...'
        for doc in documents:
            for req in doc.requirements:
                m = PRINTED_ID_RE.match(req.text)
                if m:
                    alias = (m.group(1) or f"Requirement {m.group(2)}").lower()
                    self._by_key.setdefault((_norm_doc(req.doc_id), alias), req)
                    if m.group(2):
                        self._by_key.setdefault((_norm_doc(req.doc_id), m.group(2).lower()), req)
        # (normalised doc ID, where the text names it); 'X' names all of 'X Part 1A', 'X Part 2A' unless X is loaded
        ids = [_norm_doc(d.doc_id) for d in documents]
        self._doc_patterns = []
        for d in ids:
            m = PART_ID_RE.fullmatch(d)
            loaded_whole = bool(m) and any(re.fullmatch(re.escape(m[1]) + "[A-Z]?", x) for x in ids)
            self._doc_patterns.append((d, doc_pattern(d, bare=not loaded_whole)))

        # sibling records per clause, in document order (deleted placeholders left out)
        self._siblings: dict[int, tuple[list[Requirement], int]] = {}
        for doc in documents:
            groups: dict[str, list[Requirement]] = {}
            for req in doc.requirements:
                if req.clause and req.kind != "deleted":
                    groups.setdefault(req.clause, []).append(req)
            for group in groups.values():
                for i, req in enumerate(group):
                    self._siblings[id(req)] = (group, i)

        # synthetic owners of tables that no record owns (kind "table"); not in doc.requirements, created once
        self._table_synth: dict[int, Requirement] = {}
        # BM25 entries: one per requirement record, one per table row (owned by a record or the table itself)
        self._reqs: list[tuple[Requirement, Counter, int]] = []
        self._rows: list[tuple[Table, TableRow, list[Requirement], Counter, int]] = []
        for doc in documents:
            for req in doc.requirements:
                toks = tokenize(_req_text(req))
                self._reqs.append((req, Counter(toks), len(toks)))
            by_id = {r.req_id: r for r in doc.requirements if r.kind != "deleted"}
            for t in doc.tables:
                owners = self._table_owners(doc, t)
                synthetic = owners[0].kind == "table"
                for row in t.rows:
                    text = _row_text(t, row)
                    # a requirements-matrix row restates records that are indexed themselves ('[FCR 8] ...',
                    # '[PVTR 44] ...'): not indexed, so the copy does not outrank the records (run 12: 5019A
                    # Tables 4-6, 7001C Table 3 took rank 1); the table stays available through get_table
                    if synthetic and _tagged_records(text, by_id):
                        continue
                    toks = tokenize(text)
                    self._rows.append((t, row, owners, Counter(toks), len(toks)))

        lengths = [n for *_, n in self._reqs] + [n for *_, n in self._rows]
        self._avgdl = (sum(lengths) / len(lengths)) if lengths else 1.0
        df: Counter = Counter()
        for _, toks, _ in self._reqs:
            df.update(toks.keys())
        for *_, toks, _ in self._rows:
            df.update(toks.keys())
        n = max(len(lengths), 1)
        self._idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

        self.embedder = embedder
        self.dense_weight = dense_weight
        self.reranker = reranker
        self._vectors = None  # rows: self._reqs entries, then self._rows entries
        if embedder is not None and lengths:
            texts = [_req_text(r) for r, *_ in self._reqs] + [_row_text(t, row) for t, row, *_ in self._rows]
            self._vectors = embedder.embed_documents(texts)

    @property
    def hybrid(self) -> bool:
        return self._vectors is not None

    def _table_owners(self, doc: Document, t: Table) -> list[Requirement]:
        """Requirements whose text points to the table; else the record at the table's clause; else one
        synthetic record of kind "table" (its citation is the table's), so the rows are still searchable."""
        owners = self._record_owners(doc, t)
        if owners:
            return owners
        synth = self._table_synth.get(id(t))
        if synth is None:
            synth = self._table_synth[id(t)] = Requirement(
                doc_id=t.doc_id, issue=t.issue, req_id=t.table_id, clause=t.clause, text=t.caption, page=t.page,
                kind="table")
        return [synth]

    @staticmethod
    def _record_owners(doc: Document, t: Table) -> list[Requirement]:
        key = _norm_table(t.table_id)
        pointing = [r for r in doc.requirements if r.kind != "deleted" and key in {_norm_table(x) for x in r.tables}]
        reqs = [r for r in pointing if r.kind == "requirement"]
        if reqs or pointing:
            return reqs or pointing
        return [r for r in doc.requirements if t.clause and t.clause in (r.req_id, r.clause) and r.kind != "deleted"]

    def tier_of(self, doc_id: str, issue: str) -> str:
        """Parse tier of a loaded document: "verified" (catalogue.VERIFIED, hand-checked) wins, else the
        catalogue entry's tier when its issue matches, else "unchecked"."""
        if (doc_id, issue) in VERIFIED:
            return "verified"
        e = next((e for e in self.catalogue.entries if e.doc_id == doc_id and e.issue == issue), None) \
            if self.catalogue else None
        return e.tier if e else "unchecked"

    def issue_date_of(self, doc_id: str, issue: str) -> str:
        """ISO date of the loaded edition (catalogue), "" when unknown."""
        e = next((e for e in self.catalogue.entries if e.doc_id == doc_id and e.issue == issue), None) \
            if self.catalogue else None
        return e.issue_date if e else ""

    def _edition(self, norm_id: str) -> dict:
        d = next(d for d in self.documents if _norm_doc(d.doc_id) == norm_id)
        out = {"doc_id": d.doc_id, "issue": d.issue}
        if date := self.issue_date_of(d.doc_id, d.issue):
            out["issue_date"] = date
        return out

    def split_issue(self, name: str) -> tuple[str, dict[str, str]]:
        """'ECSS-Q-ST-80C Rev.1' -> ('ECSS-Q-ST-80C', {'rev': '1'}): a document name and the issue words
        after it. A name without issue words comes back whole."""
        m = STD_ID_RE.match(HYPHENS_RE.sub("-", name.strip().upper()))
        if not m:
            return name, {}
        words = issue_words(name.strip()[m.end():])
        return (name.strip()[:m.end()], words) if words else (name, {})

    def other_letter(self, name: str) -> list[str]:
        """Loaded documents that are another issue letter of `name` ('NASA-STD-5001A' -> NASA-STD-5001B,
        'ECSS-Q-ST-80B' -> ECSS-Q-ST-80C). Empty when `name` itself is loaded or has no issue letter."""
        want = _norm_doc(name)
        if not re.search(r"\d[A-Z]$", want) or self._match_doc(name):
            return []
        return [d for d in (_norm_doc(x.doc_id) for x in self.documents)
                if d != want and re.fullmatch(re.escape(want[:-1]) + "[A-Z]?", d)]

    def issue_mismatches(self, text: str) -> list[dict]:
        """Standards named in `text` with an issue that is not the loaded one: 'ECSS-Q-ST-80C Rev.1' when
        Rev.2 is loaded, 'NASA-STD-5001A' when 5001B is. Each entry: what was asked, and the loaded edition."""
        up = HYPHENS_RE.sub("-", text.upper())
        out: list[dict] = []
        for d, pat in self._doc_patterns:
            for m in pat.finditer(up):
                asked = issue_words(text[m.end():m.end() + 40])
                ed = self._edition(d)
                if asked and issue_differs(asked, ed["issue"]):
                    said = " ".join(text[m.start():m.end() + ISSUE_SPAN(text[m.end():])].split())
                    out.append({"asked": said, **ed, "reason": "another issue of this document is loaded"})
        for m in STD_ID_RE.finditer(up):
            name = std_name(m)
            for d in self.other_letter(name):
                out.append({"asked": name, **self._edition(d), "reason": "another revision letter is loaded"})
        seen, uniq = set(), []
        for x in out:
            if (x["asked"], x["doc_id"]) not in seen:
                seen.add((x["asked"], x["doc_id"]))
                uniq.append(x)
        return uniq

    def list_documents(self, family: str = "", doc_type: str = "", discipline: str = "", query: str = "",
                       include_not_loaded: bool = False) -> list[dict]:
        """Loaded documents (record counts, family, type, discipline, parse tier), then, with
        include_not_loaded, catalogued documents that are not loaded. Filters are case-insensitive;
        discipline matches the code ("E-32", "NASA-5000") or the name ("structures")."""
        entries = {e.doc_id: e for e in self.catalogue.entries} if self.catalogue else {}
        out = []
        for d in self.documents:
            e = entries.get(d.doc_id)
            info = {**classify(d.doc_id), "tier": self.tier_of(d.doc_id, d.issue)}
            out.append({**d.summary(), **info, "title": d.title or (e.title if e else "")})
        if include_not_loaded and self.catalogue:
            loaded = {d.doc_id for d in self.documents}
            out += [{**e.to_dict(), "loaded": False} for e in self.catalogue.entries
                    if e.doc_id not in loaded and e.status == "active"]

        def keep(d: dict) -> bool:
            return ((not family or d["family"].lower() == family.lower())
                    and (not doc_type or doc_type.lower() in d["doc_type"].lower())
                    and (not discipline or discipline.lower() in f"{d['discipline']} {d['discipline_name']}".lower())
                    and (not query or all(w in f"{d['doc_id']} {d['title']}".lower() for w in query.lower().split())))
        return [d for d in out if keep(d)]

    def _match_doc(self, doc_id: str, among: list[str] | None = None) -> list[str]:
        """Accept 'ECSS-Q-ST-80' for 'ECSS-Q-ST-80C' and 'NPR 7150.2' for 'NPR 7150.2D'.

        A name that is a whole ID minus its issue letter ('ECSS-E-ST-32' -> 'ECSS-E-ST-32C') matches
        only that document, not every ID that starts with it (ECSS-E-ST-32-01C, -10C, …).
        `among`: other doc IDs to match against (default: the loaded documents); normalised IDs are returned.
        """
        want = _norm_doc(doc_id)
        ids = [_norm_doc(d) for d in among] if among is not None else [_norm_doc(d.doc_id) for d in self.documents]
        exact = [d for d in ids if d == want or re.fullmatch(re.escape(want) + "[A-Z]", d)]
        # a prefix ends where a number does: 'NASA-HDBK-5010-VOL-1' is not 'NASA-HDBK-5010-VOL-10'
        return exact or [d for d in ids if d.startswith(want) and not d[len(want):len(want) + 1].isdigit()]

    def detect_documents(self, query: str) -> list[str]:
        """Loaded documents named in the query (normalised IDs)."""
        return self._detect(query)[0] or []

    def _detect(self, query: str) -> tuple[list[str] | None, bool]:
        """(documents, named explicitly) for a query; None = no restriction. A family named
        when none of its documents is loaded gives [] (search nothing, not everything).

        Matches a full ID or the ID without its issue letter, as a whole word (doc_pattern: a part, volume
        or annex by its own name, all parts by the bare number); falls back to the family when the query
        only says "ECSS" or "NASA" (and not both).
        """
        q = HYPHENS_RE.sub("-", query.upper())
        found = [d for d, pat in self._doc_patterns if pat.search(q)]
        if found:
            return found, True
        # standalone family words only: "NASA-HDBK-2203" (not loaded) is not a mention of "NASA"
        words = HYPHENS_RE.sub("-", query.upper())
        families = {f for f in ("ECSS", "NASA") if re.search(rf"(?<![A-Z0-9-]){f}(?![A-Z0-9-])", words)}
        if len(families) == 1:
            fam = families.pop()
            return [_norm_doc(d.doc_id) for d in self.documents if _family(d.doc_id) == fam], False
        return None, False

    def _docs_for(self, doc_id: str) -> list[str]:
        """Loaded documents a caller names, issue words allowed ('ECSS-Q-ST-80C Rev.2'); none when the named
        issue is not the loaded one."""
        name, asked = self.split_issue(doc_id)
        return [d for d in self._match_doc(name) if not asked or not issue_differs(asked, self._edition(d)["issue"])]

    def loaded_issues(self, doc_id: str) -> list[dict]:
        """The loaded editions of a document named with an issue or revision letter that is not loaded."""
        name, asked = self.split_issue(doc_id)
        if asked:
            return [self._edition(d) for d in self._match_doc(name) if issue_differs(asked, self._edition(d)["issue"])]
        return [self._edition(d) for d in self.other_letter(name)]

    def get(self, doc_id: str, req_id: str) -> Requirement | None:
        for d in self._docs_for(doc_id):
            req = self._by_key.get((d, req_id.strip().lower()))
            if req:
                return req
        return None

    def lookup_help(self, doc_id: str, req_id: str) -> dict:
        """What to offer when get() finds nothing in a loaded document:

        - `parent`: the record that holds the item ('5.2.2' for '5.2.2a', when the document's items were kept
          inside their paragraph);
        - `records_in_clause`: the records of a clause asked for without an item ('5.4.4' -> 5.4.4a, 5.4.4b);
        - `nearest_ids`: IDs of the same document that share the longest leading part with the one asked.
        Empty when the document is not loaded."""
        docs = self._docs_for(doc_id)
        if not docs:
            return {}
        d = docs[0]
        doc = next(x for x in self.documents if _norm_doc(x.doc_id) == d)
        want = req_id.strip().lower()
        out: dict = {}
        stem_id = want
        for _ in range(2):  # '12.3.5.c(3)' -> '12.3.5.c' -> '12.3.5'
            cut = ITEM_SUFFIX_RE.sub("", stem_id)
            if cut == stem_id or not cut:
                break
            stem_id = cut
            parent = self._by_key.get((d, stem_id))
            # the record with exactly that ID: a clause alias ('4.2' for its only record 4.2a) is a sibling
            if parent is not None and parent.req_id.lower() == stem_id:
                out["parent"] = parent
                break
        inside = [r for r in doc.requirements if r.clause.lower() == want and r.req_id.lower() != want]
        if inside:
            out["records_in_clause"] = [{"citation": r.citation, "req_id": r.req_id, "kind": r.kind} for r in inside]
        if not out:
            def shared(a: str) -> int:
                n = 0
                for x, y in zip(a.lower(), want):
                    if x != y:
                        break
                    n += 1
                return n
            ranked = sorted(doc.requirements, key=lambda r: -shared(r.req_id))
            best = shared(ranked[0].req_id) if ranked else 0
            if best >= 2:
                out["nearest_ids"] = [r.req_id for r in ranked if shared(r.req_id) == best][:8]
        return out

    def get_table(self, doc_id: str, table_id: str) -> Table | None:
        for d in self._docs_for(doc_id):
            t = self._tables.get((d, _norm_table(table_id)))
            if t:
                return t
        return None

    def list_tables(self, doc_id: str | None = None) -> list[dict]:
        allowed = set(self._match_doc(doc_id)) if doc_id else None
        return [
            {"citation": t.citation, "doc_id": t.doc_id, "issue": t.issue, "table_id": t.table_id,
             "caption": t.caption, "clause": t.clause}
            for (d, _), t in self._tables.items()
            if allowed is None or d in allowed
        ]

    def _bm25(self, q: list[str], toks: Counter, length: int) -> float:
        norm = K1 * (1 - B + B * length / self._avgdl)
        return sum(self._idf.get(t, 0.0) * toks[t] * (K1 + 1) / (toks[t] + norm) for t in q if t in toks)

    def search_hits(self, query: str, doc_id: str | None = None, limit: int = 5,
                    detect_docs: bool = True) -> list[SearchHit]:
        """Ranked requirement records. Without doc_id, documents named in the query restrict the
        search; when several are named, their rankings are interleaved so each gets a share."""
        named = False
        allowed: set[str] | None = None  # None = all documents; an empty set = none loaded matches
        if doc_id:
            allowed = set(self._match_doc(doc_id))
        elif detect_docs:
            detected, named = self._detect(query)
            if detected is not None:
                allowed = set(detected)
        if allowed is not None and not allowed:
            return []
        q = tokenize(self._subject(query) if named else query)
        # "what does ECSS mean by X", "definition of X": the term's definition is the answer, not a side note
        defining = bool(DEFINE_RE.search(query))

        best: dict[int, SearchHit] = {}
        for req, toks, n in self._reqs:
            if allowed is not None and _norm_doc(req.doc_id) not in allowed:
                continue
            s = self._bm25(q, toks, n) * (DEFINITION_ASKED if defining and req.kind == "definition" else record_weight(req))
            if s > 0:
                best[id(req)] = SearchHit(s, req, lexical=s)
        for t, row, owners, toks, n in self._rows:
            if allowed is not None and _norm_doc(t.doc_id) not in allowed:
                continue
            s = self._bm25(q, toks, n)
            if s <= 0:
                continue
            for req in owners:
                hit = best.get(id(req))
                if hit is None or s > hit.score:
                    best[id(req)] = SearchHit(s, req, t, row, lexical=s)

        hits = sorted(best.values(), key=lambda h: h.score, reverse=True)
        if self.hybrid and query.strip():
            hits = self._fuse(query, hits, allowed)
        if self.reranker is not None and query.strip() and hits:
            hits = self._rerank(query, hits)
        for h in hits:
            h.score = round(h.score, 3)
            h.lexical = round(h.lexical, 3)
        docs = list(dict.fromkeys(_norm_doc(h.requirement.doc_id) for h in hits))
        if named and len(docs) > 1:
            per_doc = [[h for h in hits if _norm_doc(h.requirement.doc_id) == d] for d in docs]
            hits = [h for group in zip_longest(*per_doc) for h in group if h]
        return hits[:limit]

    def _subject(self, query: str) -> str:
        """The query without the names of the standards it is restricted to (and their issue words): the
        name's own tokens ('npr', '7150.2') would favour records that merely cite the standard."""
        up = HYPHENS_RE.sub("-", query.upper())
        out = query
        spans = [m.span() for _, pat in self._doc_patterns for m in pat.finditer(up)]
        for a, b in sorted(spans, reverse=True):
            b += ISSUE_SPAN(out[b:])
            out = out[:a] + " " + out[b:]
        return out if tokenize(out) else query

    def _fuse(self, query: str, lexical: list[SearchHit], allowed: set[str] | None) -> list[SearchHit]:
        """Reciprocal rank fusion of the BM25 ranking and the embedding ranking (top DENSE_POOL).

        score = RRF_K * (1 / (RRF_K + bm25 rank) + dense_weight / (RRF_K + dense rank)), so a record ranked
        first by both scores about 2 and a record found by one ranking only scores at most about 1.
        """
        sims = self._vectors @ self.embedder.embed_query(query)
        dense: dict[int, tuple[float, Requirement, Table | None, TableRow | None]] = {}
        for i, (req, _, _) in enumerate(self._reqs):
            if allowed is None or _norm_doc(req.doc_id) in allowed:
                s = float(sims[i]) * record_weight(req)
                if id(req) not in dense or s > dense[id(req)][0]:
                    dense[id(req)] = (s, req, None, None)
        off = len(self._reqs)
        for j, (t, row, owners, _, _) in enumerate(self._rows):
            if allowed is not None and _norm_doc(t.doc_id) not in allowed:
                continue
            s = float(sims[off + j])
            for req in owners:
                if id(req) not in dense or s > dense[id(req)][0]:
                    dense[id(req)] = (s, req, t, row)
        dense_ranked = sorted(dense.values(), key=lambda x: x[0], reverse=True)[:DENSE_POOL]

        fused = {id(h.requirement): h for h in lexical}
        for rank, h in enumerate(lexical, 1):
            h.score = RRF_K / (RRF_K + rank)
        for rank, (s, req, t, row) in enumerate(dense_ranked, 1):
            h = fused.get(id(req))
            if h is None:
                h = fused[id(req)] = SearchHit(0.0, req, t, row)
            elif h.table is None and t is not None:
                h.table, h.row = t, row
            h.score += self.dense_weight * RRF_K / (RRF_K + rank)
        for key, (s, *_) in dense.items():
            if key in fused:
                fused[key].dense = round(s, 3)
        return sorted(fused.values(), key=lambda h: (h.score, h.lexical), reverse=True)

    def _rerank(self, query: str, hits: list[SearchHit]) -> list[SearchHit]:
        """Reorder the top RERANK_POOL hits by cross-encoder score (the matched table row's text is added
        to a hit that came through a table). The rest keep their order below. `score` stays the
        first-stage score; `rerank` holds the cross-encoder's."""
        head, tail = hits[:RERANK_POOL], hits[RERANK_POOL:]
        texts = [_req_text(h.requirement) + (" " + _row_text(h.table, h.row) if h.table and h.row else "")
                 for h in head]
        for h, s in zip(head, self.reranker.score(query, texts)):
            h.rerank = round(s, 3)
        return sorted(head, key=lambda h: h.rerank, reverse=True) + tail

    def neighbours(self, req: Requirement, window: int = NEIGHBOURS) -> list[Requirement]:
        """Records next to `req` in the same clause: up to `window` before and after it."""
        group, i = self._siblings.get(id(req), ([], 0))
        return group[max(0, i - window): i] + group[i + 1: i + 1 + window]

    def _hit_dicts(self, hits: list[SearchHit]) -> list[dict]:
        """Hits as tool results, each with its `neighbours` (full records, so they can be cited) unless
        another hit or an earlier hit's neighbours already show them."""
        shown = {id(h.requirement) for h in hits}
        out = []
        for h in hits:
            d = h.to_dict()
            near = [r for r in self.neighbours(h.requirement) if id(r) not in shown]
            shown.update(id(r) for r in near)
            if near:
                d["neighbours"] = [r.to_dict() for r in near]
            out.append(d)
        return out

    def mentioned_not_loaded(self, query: str) -> list[str]:
        """Standard IDs named in the query that match no loaded document ('ECSS-E-ST-33-01',
        'NASA-STD-7003', 'ECSS-E-HB-32-20 Part 3A' when only Part 1A is loaded): results for such a query
        come from other documents (hand test F6)."""
        out = []
        for m in STD_ID_RE.finditer(HYPHENS_RE.sub("-", query.upper())):
            name = std_name(m)
            if not self._match_doc(name) and name not in out:
                out.append(name)
        return out

    def not_loaded_report(self, names: list[str]) -> tuple[dict, list[str]]:
        """Fields and notes for standards that are named but not loaded (step A6).

        Always `not_loaded` (the names). With a catalogue, also split them by the documents folder:
        `in_documents_folder` (name -> the catalogued documents it matches, with issue and status; an
        active one can be loaded through corpus.yaml, a superseded one never is) and
        `not_in_documents_folder` (names the folder does not hold at all).
        """
        if not names:
            return {}, []
        out: dict = {"not_loaded": names}
        if self.catalogue is None:
            return out, [f"Not loaded: {', '.join(names)}. Do not answer from these standards."]
        loaded = {_norm_doc(d.doc_id) for d in self.documents}
        entries = {_norm_doc(e.doc_id): e for e in self.catalogue.entries if _norm_doc(e.doc_id) not in loaded}
        present, absent = [], []
        for name in names:
            matched = self._match_doc(name, list(entries))
            if matched:
                present.append({"name": name, "documents": [
                    {"doc_id": entries[m].doc_id, "issue": entries[m].issue, "title": entries[m].title,
                     "status": entries[m].status} for m in matched]})
            else:
                absent.append(name)
        notes = []
        if present:
            out["in_documents_folder"] = present
            active = [p["name"] for p in present if any(d["status"] == "active" for d in p["documents"])]
            superseded = [p["name"] for p in present if p["name"] not in active]
            if active:
                notes.append(f"In the documents folder but not loaded: {', '.join(active)}. Their text is not "
                             "available: do not answer from them. You may name them as the standards that would "
                             "cover the question; the user can load them through corpus.yaml.")
            if superseded:
                notes.append(f"Only a superseded issue is in the documents folder (never loaded): "
                             f"{', '.join(superseded)}. Do not answer from them.")
        if absent:
            out["not_in_documents_folder"] = absent
            notes.append(f"Not in the documents folder: {', '.join(absent)}. Do not answer from these standards.")
        return out, notes

    def external_standards(self, query: str) -> list[str]:
        """Standards of other bodies named in the query (SMC-S-016, MIL-STD-1540, ISO 24113, MISRA C)."""
        up = STD_ID_RE.sub(" ", HYPHENS_RE.sub("-", query.upper()))
        return list(dict.fromkeys(" ".join(m.group(0).split()) for m in EXTERNAL_STD_RE.finditer(up)))

    def unmatched_designations(self, query: str, hits: list[SearchHit]) -> list[str]:
        """Acronyms and designations in the query (words in capitals, alloy or part designations such as
        '7075-T7351') that no returned hit, neighbour or matched table row contains. A subject named this
        way and found in no hit is probably not treated by the hits."""
        raw = HYPHENS_RE.sub("-", query)
        up = raw.upper()
        for _, pat in self._doc_patterns:  # loaded documents' own names are not subjects
            for m in pat.finditer(up):
                raw = raw[:m.start()] + " " * (m.end() - m.start()) + raw[m.end():]
        raw = EXTERNAL_STD_RE.sub(" ", STD_ID_RE.sub(" ", raw))
        raw = re.sub(r"(?i)\b(?:rev(?:ision)?\.?|change|corr\.?|part|vol(?:ume)?\.?|table|annex)\s*[A-Z0-9-]+", " ", raw)
        names = [m.group(0) for m in DESIGNATION_RE.finditer(raw) if m.group(0) not in PLAIN_CAPS]
        if not names:
            return []
        pool: set[str] = set()
        for h in hits:
            pool.update(tokenize(_req_text(h.requirement)))
            if h.table is not None and h.row is not None:
                pool.update(tokenize(_row_text(h.table, h.row)))
            for n in self.neighbours(h.requirement):
                pool.update(tokenize(_req_text(n)))
        return [n for n in dict.fromkeys(names) if not set(tokenize(n)) & pool]

    def search_response(self, query: str, doc_id: str | None = None, limit: int = 5) -> dict:
        """search_hits plus what a client needs to judge coverage (hand test F6):

        - `not_loaded`: standards named in the query that are not loaded; with a catalogue, split into
          `in_documents_folder` and `not_in_documents_folder` (not_loaded_report);
        - `elsewhere`: when the query names loaded documents but their best match scores well below
          the best match in other documents (e.g. a topic the named standard does not treat), the top
          hits from the other documents, kept apart from the filtered `results`.
        """
        hits = self.search_hits(query, doc_id, limit)
        out: dict = {"results": self._hit_dicts(hits)}
        missing, notes = self.not_loaded_report(self.mentioned_not_loaded(query))
        out.update(missing)
        if missing:
            notes.append("Results come from the loaded documents only and may not cover the question.")
        external = self.external_standards(query)
        if external:
            out["external_standards"] = external
            notes.append(f"Not an ECSS or NASA document held here: {', '.join(external)}. Loaded standards may "
                         "refer to it but do not reproduce it: do not state its requirements.")
        unmatched = self.unmatched_designations(query, hits)
        if not any(h.lexical > 0 for h in hits):  # keyword matches only: an embedding always finds a neighbour
            out["coverage"] = "none"
            notes.append("No loaded record matches this query. Say the loaded standards do not cover it, or "
                         "search again with other words.")
        elif unmatched:
            out["coverage"] = "weak"
            out["unmatched_terms"] = unmatched
            notes.append(f"No hit contains {', '.join(unmatched)}: the hits may not treat that subject. Search "
                         "for it by another name; if nothing returned treats it, say the loaded standards do "
                         "not cover it.")
        mismatch = self.issue_mismatches(" ".join(filter(None, [query, doc_id])))
        if mismatch:
            out["issue_mismatch"] = mismatch
            notes.append("The question names an issue that is not loaded: " + "; ".join(
                f"{x['asked']} (loaded: {x['doc_id']} {x['issue'] or 'first issue'}"
                + (f", {x['issue_date']}" if x.get("issue_date") else "") + ")" for x in mismatch)
                + ". Results come from the loaded issue; its clause numbers and text can differ from the issue "
                "asked about. Say so, and do not present them as the issue asked about.")
        detected, named = self._detect(query) if not doc_id else (set(self._match_doc(doc_id)), True)
        if named and detected:
            # compare on the topic words only: the ID's own tokens ('nasa', 'std') would favour
            # other documents that cite the named standard
            topic = STD_ID_RE.sub(" ", HYPHENS_RE.sub("-", query.upper()))
            scope = set(detected)
            ranked = self.search_hits(topic, limit=len(self._reqs), detect_docs=False)
            # lexical scores: the threshold was calibrated on BM25 (hybrid ranks, but does not judge coverage)
            inside = max((h.lexical for h in ranked if _norm_doc(h.requirement.doc_id) in scope), default=0.0)
            others = [h for h in ranked if _norm_doc(h.requirement.doc_id) not in scope]
            outside = max((h.lexical for h in others), default=0.0)
            if others and inside < WEAK_RATIO * outside:
                out["elsewhere"] = [h.to_dict() for h in others[:3]]
                notes.append("The named document(s) match this query weakly; stronger matches are in other "
                             "loaded documents (see 'elsewhere'). The named document may not cover the topic.")
        if notes:
            out["notes"] = notes
        return out

    def compare_topic(self, topic: str, doc_ids: list[str] | None = None, limit: int = 5) -> dict:
        """One topic searched separately in each document, for side-by-side comparison (ECSS vs NASA).

        Documents: `doc_ids` (each may expand, e.g. 'ECSS-E-ST-32-01' or just 'NASA'), else the loaded
        documents named in the topic when there are two or more, else all loaded documents. Standard
        names are removed from the topic before ranking, so each document is scored on the subject only.
        A section's `coverage` is 'none' (no hit), 'weak' (best hit below WEAK_RATIO × the best hit in
        any compared document: it may not treat the topic) or 'ok'.
        """
        out: dict = {"topic": topic}
        not_loaded: list[str] = []
        if doc_ids:
            docs: list[str] = []
            for d in doc_ids:
                matched = self._match_doc(d)
                if not matched:
                    not_loaded.append(d)
                docs.extend(m for m in matched if m not in docs)
        else:
            named, explicit = self._detect(topic)
            docs = named if explicit and named and len(named) > 1 else [_norm_doc(d.doc_id) for d in self.documents]
        not_loaded += [m for m in self.mentioned_not_loaded(topic) if m not in not_loaded]

        subject = STD_ID_RE.sub(" ", HYPHENS_RE.sub("-", topic.upper()))
        subject = re.sub(r"(?<![A-Z0-9-])(?:ECSS|NASA|VS|VERSUS|COMPARE|COMPARED)(?![A-Z0-9-])", " ", subject)
        chosen = False
        if not doc_ids and len(docs) > COMPARE_DOCS:
            # a large corpus: compare the standards that say most on the subject, COMPARE_PER_FAMILY per family
            # (named documents first), instead of one section for every loaded document
            # two or more named documents were kept above; a single named one is added to the best matches
            keep = [d for d in docs if len(docs) < len(self.documents)] or [d for d in (named or []) if explicit and d in docs][:1]
            for fam in ("ECSS", "NASA"):
                ranked = [_norm_doc(x["doc_id"]) for x in self.rank_documents(subject, family=fam, limit=COMPARE_PER_FAMILY)]
                keep += [d for d in ranked if d not in keep]
            docs, chosen = keep, True
        by_id = {_norm_doc(d.doc_id): d for d in self.documents}
        sections = []
        for d in docs:
            hits = self.search_hits(subject, doc_id=by_id[d].doc_id, limit=limit)
            sections.append({"doc_id": by_id[d].doc_id, "issue": by_id[d].issue, "family": _family(d) or "other",
                             "title": by_id[d].title, "results": self._hit_dicts(hits),
                             "_best": max((h.lexical for h in hits), default=0.0)})
        # coverage on BM25 scores, as calibrated (with hybrid search, dense-only hits have lexical 0)
        top = max((s["_best"] for s in sections), default=0.0)
        for s in sections:
            best = s.pop("_best")
            s["coverage"] = "none" if not best else "weak" if best < WEAK_RATIO * top else "ok"
        order = {"ECSS": 0, "NASA": 1}
        sections.sort(key=lambda s: order.get(s["family"], 2))  # stable: keeps the requested order inside a family
        out["documents"] = sections
        missing, notes = self.not_loaded_report(not_loaded)
        out.update(missing)
        if missing:
            notes.append("Do not compare against standards that are not loaded.")
        if chosen:
            out["documents_chosen"] = "top matches per family"
            notes.append(f"No doc_ids given: compared the {COMPARE_PER_FAMILY} standards per family that match the "
                         "topic best (find_standards ranks more). Pass doc_ids to compare specific standards.")
        if any(s["coverage"] != "ok" for s in sections):
            notes.append("Documents marked 'weak' or 'none' may not treat this topic; say so instead of "
                         "presenting their hits as equivalents.")
        if notes:
            out["notes"] = notes
        return out

    def rank_documents(self, topic: str, family: str = "", doc_type: str = "", limit: int = 8,
                       pool: int = DOC_POOL) -> list[dict]:
        """Loaded standards ranked by how much they say on a topic ("which standards apply to ...").

        Score: the three best keyword matches of a document among the top `pool` records (handbook and
        guidance weights as in search), plus a title share: the part of the topic's words found in the
        title, times the best match overall. Each entry names its best-matching sections (clause, heading,
        the record to open); no requirement text. Standards named in the topic do not restrict the ranking."""
        subject = STD_ID_RE.sub(" ", HYPHENS_RE.sub("-", topic.upper())).lower()
        words = set(tokenize(subject))
        hits = self.search_hits(subject, limit=pool, detect_docs=False) if words else []
        top = max((h.lexical for h in hits), default=0.0)
        per_doc: dict[str, list[SearchHit]] = {}
        for h in hits:
            per_doc.setdefault(h.requirement.doc_id, []).append(h)
        entries = {e.doc_id: e for e in self.catalogue.entries} if self.catalogue else {}
        out = []
        for d in self.documents:
            info = classify(d.doc_id)
            if (family and info["family"].lower() != family.lower()) or (
                    doc_type and doc_type.lower() not in info["doc_type"].lower()):
                continue
            title = d.title or (entries[d.doc_id].title if d.doc_id in entries else "")
            in_title = len(words & set(tokenize(title))) / len(words) if words else 0.0
            mine = per_doc.get(d.doc_id, [])
            score = sum(h.lexical for h in mine[:3]) + in_title * (top or 1.0)
            if not mine and in_title < 0.5:
                continue
            sections, seen = [], set()
            for h in mine:
                r = h.requirement
                if r.clause in seen:
                    continue
                seen.add(r.clause)
                sections.append({"clause": r.clause, "heading": r.heading_path[-1] if r.heading_path else "",
                                 "citation": r.citation, "kind": r.kind})
                if len(sections) == 3:
                    break
            out.append({"doc_id": d.doc_id, "issue": d.issue, "title": title, **info,
                        "tier": self.tier_of(d.doc_id, d.issue), "score": round(score, 2),
                        "matching_records": len(mine), "top_sections": sections})
        out.sort(key=lambda x: x["score"], reverse=True)
        return out[:limit]

    def section_outline(self, doc_id: str, clause: str = "", depth: int = 2) -> dict | None:
        """Heading tree of one document (from the records' heading paths), for browsing a clause
        instead of guessing search terms. None when the document is not loaded.

        Each section: clause number, title, depth (1 = top-level clause), records in its subtree
        by kind. With `clause`, only that section and its subsections, plus the records placed
        directly in it (IDs and kinds, no text) and the tables in its subtree. `depth` limits how
        many levels below the starting point are listed.
        """
        matched = self._match_doc(doc_id)
        doc = next((d for d in self.documents if matched and _norm_doc(d.doc_id) == matched[0]), None)
        if doc is None:
            return None
        want = clause.strip().rstrip(".").lower()

        def inside(num: str) -> bool:
            return not want or num.lower() == want or num.lower().startswith(want + ".")

        sections: dict[tuple[str, ...], dict] = {}
        for r in doc.requirements:
            for i in range(len(r.heading_path)):
                key = tuple(r.heading_path[: i + 1])
                s = sections.get(key)
                if s is None:
                    m = HEADING_RE.match(key[-1])
                    num, title = (m.group(1), (m.group(2) or "").strip()) if m else ("", key[-1])
                    s = sections[key] = {"clause": num, "title": title, "depth": i + 1, "kinds": Counter()}
                s["kinds"][r.kind] += 1

        listed = [s for s in sections.values() if s["clause"] and inside(s["clause"])]
        if want and not listed:
            return {"found": False, "doc_id": doc.doc_id, "issue": doc.issue,
                    "message": f"No clause {clause} in {doc.doc_id} among parsed headings."}
        base = min((s["depth"] for s in listed), default=1)
        out: dict = {"found": True, "doc_id": doc.doc_id, "issue": doc.issue}
        if doc.title:
            out["title"] = doc.title
        out["sections"] = [
            {"clause": s["clause"], "title": s["title"], "depth": s["depth"],
             "records": sum(s["kinds"].values()), "kinds": dict(s["kinds"])}
            for s in listed if s["depth"] < base + max(depth, 1)
        ]
        if want:
            out["clause"] = want
            out["records"] = [{"citation": r.citation, "req_id": r.req_id, "kind": r.kind}
                              for r in doc.requirements if r.clause.lower() == want]
            # a NASA table's clause is the tag that points to it ('FSR 24'): place it at that record's clause
            where = {r.req_id: r.clause for r in doc.requirements}
            out["tables"] = [{"citation": t.citation, "table_id": t.table_id, "caption": t.caption}
                             for t in doc.tables if t.clause and inside(where.get(t.clause, t.clause))]
        return out

    def search(self, query: str, doc_id: str | None = None, limit: int = 5,
               detect_docs: bool = True) -> list[tuple[float, Requirement]]:
        return [(h.score, h.requirement) for h in self.search_hits(query, doc_id, limit, detect_docs)]
