"""Turn a document's paragraphs into requirement records.

v0 rules (see docs/ARCHITECTURE.md):
- "5.2.1 Title"        -> numbered heading, sets the current clause
- "a. text"            -> ECSS-style requirement, id = clause + letter (e.g. 5.2.1a)
- "NOTE ..."           -> attached to the last requirement
- "text [SWE-033]"     -> NASA-style requirement, id = SWE-033 (any [ABC-n] / [ABC n] tag)
- other text           -> continuation of the last requirement (if any)

Real documents will need per-document tuning; keep that in loaders or
small overrides rather than special-casing here.
"""

from __future__ import annotations

import re

from .models import Requirement

HEADING_RE = re.compile(r"^(\d+(?:\.\d+)*)\s+(\S.*)$")
ECSS_ITEM_RE = re.compile(r"^([a-z])\.\s+(\S.*)$")
# NASA-style bracketed requirement tags, e.g. [SWE-033], [FCR 12], [SFSR-3].
# Exact tag formats per NASA standard to be confirmed on the real documents.
NASA_TAG_RE = re.compile(r"\[([A-Z]{2,8}[- ]?\d{1,4})\]")
NOTE_RE = re.compile(r"^NOTE(?:\s+\d+)?\s*[:\-–]?\s*(.*)$", re.IGNORECASE)

REFERENCE_PATTERNS = [
    re.compile(r"\bECSS-[EQMU]-(?:ST|HB|TM|AS)-\d{2}(?:-\d{2})?[A-Z]?\b"),
    re.compile(r"\bNPR\s+\d{4}\.\d+[A-Z]?\b"),
    re.compile(r"\bNASA-(?:STD|HDBK)-\d{4}(?:\.\d+)?[A-Z]?\b"),
    re.compile(r"\bclause\s+\d+(?:\.\d+)+[a-z]?\b", re.IGNORECASE),
]


# Handbooks (ECSS-x-HB-nn-nn, NASA-HDBK-nnnn) have no lettered requirements: their prose is kept as one
# `guidance` record per numbered section (release plan A5).
HANDBOOK_RE = re.compile(r"^(?:ECSS-[A-Z]-HB-|NASA-HDBK-)", re.IGNORECASE)


def is_handbook(doc_id: str) -> bool:
    return bool(HANDBOOK_RE.match(doc_id.strip()))


def find_references(text: str) -> list[str]:
    text = re.sub(r"(?<=ECSS)[\u2013\u2010\u2011]|(?<=[A-Z]{2})[\u2013\u2010\u2011](?=[A-Z0-9])", "-", text)
    refs: list[str] = []
    for pattern in REFERENCE_PATTERNS:
        for match in pattern.findall(text):
            if match not in refs:
                refs.append(match)
    return refs


def _heading_level(clause: str) -> int:
    return clause.count(".") + 1


def parse_paragraphs(paragraphs: list[str], doc_id: str, issue: str, handbook: bool = False) -> list[Requirement]:
    requirements: list[Requirement] = []
    heading_path: list[str] = []
    clause = ""
    current: Requirement | None = None

    def finish(req: Requirement | None) -> None:
        if req is not None:
            req.references = find_references(" ".join([req.text, *req.notes]))

    for raw in paragraphs:
        line = " ".join(raw.split())
        if not line:
            continue

        heading = HEADING_RE.match(line)
        if heading and not NASA_TAG_RE.search(line):
            finish(current)
            current = None
            clause = heading.group(1)
            level = _heading_level(clause)
            heading_path = heading_path[: level - 1] + [line]
            continue

        if handbook and clause:  # one guidance record per numbered section: its paragraphs are the body
            note = NOTE_RE.match(line)
            if note and current is not None:
                current.notes.append(note.group(1))
            elif current is None:
                current = Requirement(doc_id, issue, clause, clause, line, list(heading_path), kind="guidance")
                requirements.append(current)
            else:
                current.text = f"{current.text}\n{line}"
            continue

        nasa = NASA_TAG_RE.search(line)
        if nasa:
            finish(current)
            text = NASA_TAG_RE.sub("", line).strip()
            current = Requirement(doc_id, issue, nasa.group(1), clause, text, list(heading_path))
            requirements.append(current)
            continue

        item = ECSS_ITEM_RE.match(line)
        if item and clause:
            finish(current)
            current = Requirement(doc_id, issue, f"{clause}{item.group(1)}", clause, item.group(2), list(heading_path))
            requirements.append(current)
            continue

        note = NOTE_RE.match(line)
        if note and current is not None:
            current.notes.append(note.group(1))
            continue

        if current is not None:
            current.text = f"{current.text} {line}"

    finish(current)
    return requirements
