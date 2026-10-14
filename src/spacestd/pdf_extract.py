"""Layout-aware PDF extraction (pdfplumber): text lines with font flags, minus page
furniture and table regions, plus the tables themselves as structured rows.

Used by the ECSS and NASA PDF parsers. Nothing here knows about requirement IDs.
"""

from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .models import Cell, Table, TableRow

HYPHENS = dict.fromkeys(map(ord, "‐‑‒−"), "-")
LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "­": ""}


# Symbol-font glyphs arrive as U+F0xx (Adobe Symbol encoding in the private-use area).
SYMBOL_GLYPHS = {
    0xF0A3: "≤", 0xF0B3: "≥", 0xF0B1: "±", 0xF0B4: "×", 0xF0B8: "÷", 0xF0B0: "°", 0xF0A5: "∞",
    0xF0B9: "≠", 0xF0BB: "≈", 0xF0AE: "→", 0xF0D6: "√", 0xF0B6: "∂",
    0xF061: "α", 0xF062: "β", 0xF067: "γ", 0xF064: "δ", 0xF044: "Δ", 0xF065: "ε", 0xF06C: "λ",
    0xF06D: "μ", 0xF070: "π", 0xF072: "ρ", 0xF073: "σ", 0xF053: "Σ", 0xF074: "τ", 0xF071: "θ",
    0xF077: "ω", 0xF057: "Ω",
}


def normalise(text: str) -> str:
    """Normalise non-ASCII hyphens (ECSS uses U+2010 in IDs), ligatures, Symbol-font glyphs and spacing."""
    text = text.translate(HYPHENS).translate(SYMBOL_GLYPHS)
    for k, v in LIGATURES.items():
        text = text.replace(k, v)
    return " ".join(text.split())


@dataclass
class Line:
    text: str
    page: int  # 1-based
    top: float
    bottom: float
    x0: float
    size: float
    bold: float  # fraction of non-space chars in a bold font
    italic: float  # fraction of non-space chars in an italic/oblique font
    font: str  # majority font name, subset prefix removed
    first_bold: bool = False  # the first character is in a bold font (note markers)

    @property
    def is_bold(self) -> bool:
        return self.bold >= 0.8

    @property
    def is_italic(self) -> bool:
        return self.italic >= 0.6


def _font(name: str) -> str:
    return name.split("+", 1)[-1]


def _is_bold(name: str) -> bool:
    return bool(re.search(r"bold|black|heavy|semibold", name, re.I))


def _is_italic(name: str) -> bool:
    return bool(re.search(r"italic|oblique", name, re.I))


def _make_line(chars: list[dict], text: str, page_no: int) -> Line | None:
    ink = [c for c in chars if c["text"].strip()]
    text = normalise(text)
    if not ink or not text:
        return None
    sizes = sorted(round(c["size"], 1) for c in ink)
    fonts = Counter(_font(c["fontname"]) for c in ink)
    return Line(
        text=text,
        page=page_no,
        top=min(c["top"] for c in ink),
        bottom=max(c["bottom"] for c in ink),
        x0=min(c["x0"] for c in ink),
        size=sizes[len(sizes) // 2],
        bold=sum(_is_bold(c["fontname"]) for c in ink) / len(ink),
        italic=sum(_is_italic(c["fontname"]) for c in ink) / len(ink),
        font=fonts.most_common(1)[0][0],
        first_bold=_first_word_bold(ink),
    )


def _cell_chars(page, bbox) -> list[dict]:
    x0, top, x1, bottom = bbox
    cropped = page.filter(lambda o: o.get("object_type") == "char"
                          and x0 <= (o["x0"] + o["x1"]) / 2 <= x1 and top <= (o["top"] + o["bottom"]) / 2 <= bottom)
    return sorted((c for c in cropped.chars if c["text"].strip()), key=lambda c: c["x0"])  # one line: left to right


def _first_word_bold(ink: list[dict]) -> bool:
    return bool(ink) and _is_bold(ink[0]["fontname"])  # the marker of a note line


# --------------------------------------------------------------------------- tables

# 'Table 4-1: Title', 'Table 1—Title', and ECSS-Q-ST-70C's separator-less 'Table 5-1 Title'
CAPTION_RE = re.compile(r"^Table\s+([A-Z]?\d+(?:-\d+)?)(?:\s*[:—–―‒]\s*|\s*-(?!\d)\s*|\s+(?=[A-Z]))(.*)$")
ROW_NUMBER_HEAD_RE = re.compile(r"^(?:no\.?|#|item)$", re.I)
ROW_NUMBER_RE = re.compile(r"^\d{1,3}[a-z]?\.?$")
VALUE_TOKEN_RE = re.compile(r"^(?:N/A|See Note|\d+(?:[.,]\d+)?(?:\s|\*|$|[a-z]))", re.I)
NUMBER_RE = re.compile(r"^(\d+(?:[.,]\d+)?)")
FOOTNOTE_LINE_RE = re.compile(r"^(\*{1,3}|[a-z])\s+(\S.*)$")
# a full-width block closing a table that is not footnotes: 'Key:' legend lines ('0 - Can be used ...')
# or 'NOTE 1 ...' paragraphs; kept as table notes instead of becoming a body row
LEGEND_START_RE = re.compile(r"^(?:Key|Legend)\s*:?$|^NOTE\b", re.I)
LEGEND_LINE_RE = re.compile(r"^(\d{1,2}|[A-Z]{1,3})\s*[-–=:]\s+(\S.*)$")
NOTE_LINE_RE = re.compile(r"^(NOTE(?:\s+\d+)?)\s+(\S.*)$")
# trailing notes blocks (H17): first lines that mark a full-width cell as notes, never a data row
NOTES_FIRST_RE = re.compile(
    r"^(?:\*|[A-Za-z]\s+\S|\(\d{1,2}\)|\d{1,2}\s+\S|NOTES?\b|Notes?:|(?:Key|Legend)\s*:|"
    r"[A-Za-z]+(?:\s[A-Za-z]+){0,2}:$|[A-Z]{1,3}\s*[=–-]\s*\S)"
)
NOTES_HEADING_RE = re.compile(r"^[A-Za-z]+(?:\s[A-Za-z]+){0,2}:$")
PAREN_NOTE_RE = re.compile(r"^\((\d{1,2})\)\s*(\S.*)$")
DIGIT_NOTE_RE = re.compile(r"^(\d{1,2})\s+(\S.*)$")
LETTER_NOTE_RE = re.compile(r"^(\*{1,3}|[A-Za-z])\s+(\S.*)$")
LEGEND_ENTRY_RE = re.compile(r"^([A-Z]{1,3})\s*[=–-]\s*(\S.*)$")
LEGEND_SPLIT_RE = re.compile(r",\s*(?=[A-Z]{1,3}\s*=\s*\S)")
LABELLED_NOTE_RE = re.compile(r"^([A-Za-z]+(?: [A-Za-z]+)? ?\d{0,2}):\s+(\S.*)$")
NUMBERED_GROUP_RE = re.compile(r"^\d+\.\s")
LIST_ITEM_RE = re.compile(r"^[-–•]\s*\S")
# Marks a footnote superscript set right after a number ('1.10' + '5' -> '1.10<SUP>5'); parse_cell
# turns it into a footnote. Not whitespace, so it survives normalise().
SUP = "⁠"
SUP_RE = re.compile(SUP + r"([A-Za-z0-9,]+)")
# Marks 1-2 small digits right after a letter ('Bays' + '1'): a footnote marker or an exponent
# ('g' + '2'); only the table's footnote keys tell them apart (parse_cell, clean_label).
LSUP = "\u2063"
LSUP_RE = re.compile(LSUP + r"(\d{1,2})")
SUPERSCRIPT_DIGITS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _resolve_lsup(text: str, footnote_keys: set[str]) -> tuple[str, list[str]]:
    """Footnote-key digits after a letter are dropped (and returned); others become superscript digits."""
    notes: list[str] = []

    def sub(m: re.Match) -> str:
        if m.group(1) in footnote_keys:
            notes.append(m.group(1))
            return ""
        return m.group(1).translate(SUPERSCRIPT_DIGITS)

    return LSUP_RE.sub(sub, text), notes


def clean_label(text: str, footnote_keys: set[str]) -> str:
    """Row-label text: footnote marks (SUP) spaced off, letter+digit markers resolved as in parse_cell."""
    text, _ = _resolve_lsup(text.replace(SUP, " "), footnote_keys)
    return normalise(text)


@dataclass
class _CellText:
    bbox: tuple[float, float, float, float]
    lines: list[tuple[str, float, bool]]  # (text, y-centre, bold)

    @property
    def raw(self) -> str:
        return " ".join(t for t, _, _ in self.lines)  # footnote superscripts still marked (SUP)

    @property
    def text(self) -> str:
        return _resolve_lsup(self.raw.replace(SUP, " "), set())[0]

    @property
    def top(self) -> float:
        return self.bbox[1]

    @property
    def bottom(self) -> float:
        return self.bbox[3]


def _cluster(values: list[float], tol: float) -> list[float]:
    out: list[float] = []
    for v in sorted(values):
        if out and v - out[-1] <= tol:
            continue
        out.append(v)
    return out


def _index(edges: list[float], v: float) -> int:
    return min(range(len(edges)), key=lambda i: abs(edges[i] - v))


def _cell_lines(page, bbox) -> list[tuple[str, float, bool]]:
    x0, top, x1, bottom = bbox
    def inside(obj):
        if obj.get("object_type") != "char":
            return False
        cx, cy = (obj["x0"] + obj["x1"]) / 2, (obj["top"] + obj["bottom"]) / 2
        return x0 <= cx <= x1 and top <= cy <= bottom

    cropped = page.filter(inside)
    chars = [c for c in cropped.chars if c["text"].strip()]
    if chars and sum(_is_rotated(c) for c in chars) > len(chars) / 2:
        return _rotated_lines(chars, (top + bottom) / 2)
    out = []
    for tl in cropped.extract_text_lines(return_chars=True):
        ink = [c for c in tl["chars"] if c["text"].strip()]
        if not ink:
            continue
        bold = sum(_is_bold(c["fontname"]) for c in ink) / len(ink) >= 0.8
        out.append((normalise(_split_size_runs(tl["text"], tl["chars"])), (tl["top"] + tl["bottom"]) / 2, bold))
    return out


def _split_size_runs(text: str, chars: list[dict]) -> str:
    """Space off a word set in a smaller size: '1,25' + subscript 'corrected' -> '1,25 corrected'.

    Short subscripts stay attached ('Jp', 'KQ'), as do footnote markers (already spaced).
    A run clearly smaller than the text (< 0.8 x) of digits, commas or letters right after a digit
    is a footnote superscript ('1.10' + '5', '1.50' + '6,7'): it gets the SUP mark.
    """
    sizes: list[float | None] = []
    j = 0
    for ch in text:
        if j < len(chars) and chars[j]["text"] == ch:
            sizes.append(chars[j]["size"])
            j += 1
        else:
            sizes.append(None)  # space inserted by the extractor
    body = max((s for s in sizes if s is not None), default=0)
    out = list(text)
    k = len(text)
    while k > 0:  # walk runs from the end so insertions keep earlier indexes valid
        end = k
        while k > 0 and sizes[k - 1] is not None and body - sizes[k - 1] > 1.5:
            k -= 1
        run = text[k:end]
        if (end > k and k > 0 and text[k - 1].isdigit() and re.fullmatch(r"[A-Za-z0-9,]+", run)
                and not (run.isalpha() and len(run) >= 3)  # a word subscript, spaced below
                and all(s < 0.8 * body for s in sizes[k:end])):
            out.insert(k, SUP)
        elif (end > k and k > 0 and text[k - 1].isalpha() and re.fullmatch(r"\d{1,2}", run)
                and all(s < 0.8 * body for s in sizes[k:end])):
            out.insert(k, LSUP)
        elif end > k and run.isalpha() and len(run) >= 3 and k > 0 and text[k - 1] != " ":
            out.insert(k, " ")
        if end == k:
            k -= 1
    return "".join(out)


def _is_rotated(c: dict) -> bool:
    """Turned 90 deg: pdfplumber may still say upright, but the matrix is (0, +-1, -+1, 0)."""
    m = c.get("matrix")
    return (not c.get("upright", True)) or bool(m and abs(m[0]) < 0.1 and abs(m[1]) > 0.9)


def _rotated_lines(chars: list[dict], centre: float) -> list[tuple[str, float, bool]]:
    """Text turned 90 deg, one line per x column. Reads bottom to top (matrix b > 0, the default: lines
    left to right) or top to bottom (b < 0: lines right to left). Glyph sizes vary per letter, so columns
    group by x0 (within 0.25 x glyph width); a word gap is above 0.12 x glyph width along the baseline."""
    down = sum((c["matrix"][1] < 0) for c in chars if c.get("matrix")) > len(chars) / 2
    cols: list[list[dict]] = []
    for c in sorted(chars, key=lambda c: c["x0"]):
        if cols and c["x0"] - cols[-1][0]["x0"] < 0.25 * (c["x1"] - c["x0"]):
            cols[-1].append(c)
        else:
            cols.append([c])
    if down:
        cols.reverse()
    out = []
    for col in cols:
        col.sort(key=(lambda c: c["top"]) if down else (lambda c: -c["bottom"]))
        text, last = "", None
        for c in col:
            if last is not None:
                gap = c["top"] - last["bottom"] if down else last["top"] - c["bottom"]
                if gap > 0.12 * (c["x1"] - c["x0"]):
                    text += " "  # word gap along the rotated baseline
            text += c["text"]
            last = c
        bold = sum(_is_bold(c["fontname"]) for c in col) / len(col) >= 0.8
        out.append((normalise(text), centre, bold))
    return out


def parse_cell(text: str, footnote_keys: set[str]) -> Cell:
    """'1,25 a, e' -> value 1.25, footnotes [a, e]; '1.0*' -> 1.0, ['*']; 'N/A or 1.05**' keeps text."""
    text = normalise(text)
    notes: list[str] = []
    m = re.search(r"(\*+)$", text)
    if m and m.group(1) in footnote_keys:
        notes.append(m.group(1))
    # superscript markers set after a number (SUP): kept as footnotes whether or not the table
    # defines them, and never fused into the value
    text, lnotes = _resolve_lsup(text, footnote_keys)
    notes.extend(lnotes)
    sup = SUP_RE.findall(text)
    if sup:
        text = normalise(SUP_RE.sub("", text).replace(SUP, ""))
        notes.extend(x for grp in sup for x in grp.split(",") if x)
    letters = "".join(sorted(k for k in footnote_keys if len(k) == 1 and k.isalpha()))
    if letters:
        # trailing markers separated by a space: '1,25 a, e', '1,25corrected b', 'See Note c'
        m2 = re.search(rf"\s([{letters}](?:\s*,\s*[{letters}])*)$", text)
        if m2:
            notes.extend(x.strip() for x in m2.group(1).split(","))
    value = None
    if not re.search(r"\bor\b|\bto\b", text):
        n = NUMBER_RE.match(text)
        if n:
            value = float(n.group(1).replace(",", "."))
    return Cell(text=text, value=value, footnotes=notes)


def _segment(cell: _CellText, anchors: list[float], is_value: bool, tol: float = 3.0) -> dict[float, str] | None:
    """Split a cell over the logical rows (anchors) it spans.

    Returns None when the cell spans its rows as one value (a vertically centred
    'See Note c' or 'Satellite'); otherwise text per row. Lines above the first aligned
    line are a prefix shared by all sub-rows ('Man-rated S/C' above 'Launch'/'On Orbit').
    """
    inside = [a for a in anchors if cell.top - 0.5 <= a <= cell.bottom + 0.5]
    if len(inside) < 2:
        return None
    aligned = []
    for text, y, _ in cell.lines:
        near = min(inside, key=lambda a: abs(a - y))
        aligned.append(near if abs(near - y) <= tol else None)
    hits = {a for a in aligned if a is not None}
    if not hits:
        return None
    # a sub-row name wrapped over two lines, centred on its value: consecutive unaligned lines whose
    # mean y is within the tolerance of an anchor without a line of its own are that anchor's text
    if len(hits) < len(inside) and None in aligned:
        trial, k = list(aligned), 0
        while k < len(trial):
            if trial[k] is not None:
                k += 1
                continue
            j = k
            while j < len(trial) and trial[j] is None:
                j += 1
            mean = sum(y for _, y, _ in cell.lines[k:j]) / (j - k)
            taken = {x for x in trial if x is not None}
            near = min((a for a in inside if a not in taken), key=lambda a: abs(a - mean), default=None)
            if near is not None and abs(near - mean) <= tol:
                trial[k:j] = [near] * (j - k)
            k = j
        if {a for a in trial if a is not None} == set(inside):
            aligned, hits = trial, set(inside)
    fill_down = False
    if len(cell.lines) == 1:
        return None  # merged cell with one value: it applies to every row it spans
    elif len(hits) < len(inside) and (not is_value or any(not re.fullmatch(r"[\d.,\s*]+", t) for t, _, _ in cell.lines)):
        # (a value cell of plain numbers keeps a blank where it has no line; text in a value column is a label)
        n_aligned = sum(a is not None for a in aligned)
        if len(hits) < 2 or n_aligned < len(aligned) - n_aligned or len(inside) - len(hits) >= len(hits):
            return None  # a wrapped label ('FRP parts / (away from / ...') rather than sub-row labels
        fill_down = True  # sub-row labels that skip a repeated one: the line above carries on
    prefix: list[str] = []
    seg: dict[float, list[str]] = {}
    current = None
    for (text, _, _), a in zip(cell.lines, aligned):
        if a is not None:
            current = a
            seg.setdefault(a, []).append(text)
        elif current is None:
            prefix.append(text)
        else:
            seg[current].append(text)
    out = {a: " ".join(prefix + seg.get(a, [])) if seg.get(a) else ("" if not prefix else " ".join(prefix)) for a in inside}
    if fill_down:
        last = ""
        for a in sorted(inside):
            if seg.get(a):
                last = out[a]
            elif last:
                out[a] = last
    return out


def _list_labels(cell: _CellText, inside: list[float], others: list[_CellText]) -> dict[float, str] | None:
    """A label cell that lists the sub-rows repeated in every band of the next label column.

    32-10 Table 4-4: 'Joints and inserts: / - Failure / - Gapping/Sliding (Safety Critical) /
    - Gapping/Sliding (other)' spans three vehicle bands (Satellite, Launch vehicle, Man-rated),
    each with those three sub-rows. Returns the label per row anchor, or None.
    """
    head: list[str] = []
    items: list[list[str]] = []
    for text, _, _ in cell.lines:
        if LIST_ITEM_RE.match(text):
            items.append([text])
        elif items:
            items[-1].append(text)
        else:
            head.append(text)
    k = len(items)
    if k < 2 or len(inside) < 2 * k or len(inside) % k:
        return None
    bands = [o for o in others if o.top >= cell.top - 0.5 and o.bottom <= cell.bottom + 0.5 and o.lines]
    sizes = [sum(o.top - 0.5 <= a <= o.bottom + 0.5 for a in inside) for o in bands]
    if not bands or any(n != k for n in sizes) or sum(sizes) != len(inside):
        return None  # no band column confirming the repetition
    names = [" ".join(head + it) for it in items]
    return {a: names[n % k] for n, a in enumerate(sorted(inside))}


def extract_table(page, tbl, table_id: str, caption: str, doc_id: str, issue: str, page_no: int,
                  extra_footnotes: dict[str, str] | None = None) -> Table:
    raw = list(dict.fromkeys(tuple(round(v, 1) for v in c) for c in tbl.cells))
    cells = [_CellText(b, _cell_lines(page, b)) for b in raw]
    xs = _cluster([c.bbox[0] for c in cells] + [c.bbox[2] for c in cells], 1.5)
    ys = _cluster([c.top for c in cells] + [c.bottom for c in cells], 1.5)
    span = {}
    for i, c in enumerate(cells):
        span[i] = (_index(xs, c.bbox[0]), _index(xs, c.bbox[2]), _index(ys, c.top), _index(ys, c.bottom))
    ncols = len(xs) - 1

    # footnote block: a notes cell at the bottom (markers, legend, 'NOTES:' heading lines)
    footnotes: dict[str, str] = dict(extra_footnotes or {})
    foot_cells = set()

    def alone_in_rows(i: int) -> bool:
        r0, r1 = span[i][2], span[i][3]
        return not any(j != i and cells[j].lines and span[j][2] < r1 and span[j][3] > r0
                       and not (_notes_first(cells[j]) and span[j][1] - span[j][0] >= max(2, ncols / 2))
                       for j in range(len(cells)))

    floor = len(ys) - 1  # the notes chain reaches up to this grid row
    for i in sorted(range(len(cells)), key=lambda i: -span[i][3]):
        c = cells[i]
        c0, c1, r0, r1 = span[i]
        if not (c.lines and ncols > 1):
            continue
        old = c0 == 0 and c1 == ncols and (
            FOOTNOTE_LINE_RE.match(c.lines[0][0]) or (LEGEND_START_RE.match(c.lines[0][0]) and r1 == len(ys) - 1))
        new = c1 - c0 >= max(2, ncols / 2) and _notes_first(c) and r1 >= floor and alone_in_rows(i)
        if old or new:
            foot_cells.add(i)
            floor = min(floor, r0)
            _parse_notes([_resolve_lsup(t, set())[0] for t, _, _ in c.lines], footnotes)
    # a key block at the bottom of a matrix (10-03C Tables 5-1 / 5-3 / 5-5): cells of 'a ...' lines naming
    # the column letters (one wide cell, or several side by side), a bold heading cell right above them,
    # and beside them a narrow 'Key' / 'R Required' legend cell: every text cell of those grid rows is a footnote
    texts = [i for i in range(len(cells)) if cells[i].lines and i not in foot_cells]
    keyed = [i for i in texts if span[i][3] == floor and FOOTNOTE_LINE_RE.match(cells[i].lines[0][0])
             and cells[i].lines[0][0][0].islower()]
    if (keyed and min(span[i][0] for i in keyed) == 0 and len({span[i][2] for i in keyed}) == 1
            and sum(span[i][1] - span[i][0] for i in keyed) >= max(2, ncols / 2)):
        top = span[keyed[0]][2]
        head = next((i for i in texts if span[i][0] == 0 and span[i][3] == top and span[i][1] - span[i][0] >= ncols / 2
                     and all(b for _, _, b in cells[i].lines)), None)
        if head is not None:
            top = span[head][2]
        band = sorted((i for i in texts if span[i][2] >= top and span[i][3] <= floor), key=lambda i: (span[i][0], cells[i].top))
        if not any(span[i][2] < top < span[i][3] for i in texts):  # no cell reaches into the band from above
            key_cells = [i for i in band if i in keyed or i == head]
            for group in (key_cells, [i for i in band if i not in key_cells]):
                lines = [_resolve_lsup(t, set())[0] for i in group for t, _, _ in cells[i].lines]
                if group is key_cells:  # 'a Electronic ... d Valves ... g ...': key entries side by side
                    parts = [x for ln in lines for x in re.split(r"\s+(?=[a-z]\s+[A-Z])", ln)]
                    lines = ([x for x in parts if not FOOTNOTE_LINE_RE.match(x)]  # the heading first
                             + sorted((x for x in parts if FOOTNOTE_LINE_RE.match(x)), key=lambda x: x[:1]))
                if lines:
                    _parse_notes(lines, footnotes)
            foot_cells.update(band)
            floor = top
    keys = set(footnotes)

    def numeric(c: _CellText) -> bool:
        return any(VALUE_TOKEN_RE.match(t) for t, _, _ in c.lines)

    def header_like(c: _CellText) -> bool:
        return bool(c.lines) and all(b for _, _, b in c.lines) and not numeric(c)

    # group-heading rows: below row 0, one bold text cell spanning every column; it ends the header
    # and labels the data rows under it (a 'Group' label column)
    group_cells: dict[int, str] = {}
    group_parts: set[int] = set()  # further cells of a group heading cut into pieces
    header_groups: set[int] = set()  # group labels printed inside the header band
    for i, c in enumerate(cells):
        c0, c1, r0, r1 = span[i]
        if not (r0 >= 1 and c0 == 0 and ncols > 1 and c.lines and i not in foot_cells):
            continue
        # a spanning heading (first line bold), or a label in column 0 only, all lines bold, with
        # empty cells (one spanning or one per column) elsewhere in the row (ECSS-E-ST-10-03C)
        lead = (c1 == ncols and len(c.lines) == 1 and not c.lines[0][2] and NUMBERED_GROUP_RE.match(c.lines[0][0])
                and _first_word_bold(_cell_chars(page, c.bbox)))  # '1. Temperature' bold, 'Low  High' roman
        if (c1 == ncols and c.lines[0][2]) or lead or all(b for _, _, b in c.lines):
            others = [j for j in range(len(cells)) if j != i and cells[j].lines and span[j][2] < r1 and span[j][3] > r0]
            # bold header cells starting in row 0 that end where this label ends: the label shares their
            # band (7002B 'MECHANICAL TESTS' beside 'COMPONENT' ...); it is the first group, not a column name
            straddle = [j for j in others if span[j][2] == 0 and r0 == 1 and span[j][3] == r1
                        and all(b for _, _, b in cells[j].lines) and not numeric(cells[j])]
            others = [j for j in others if j not in straddle]
            # a bold bar cut into adjacent cells by fine column edges (7002B 'EMI' | '/EMC' | 'TESTS')
            chain, end = [], c1
            for j in sorted(others, key=lambda j: span[j][0]):
                if span[j][0] == end and span[j][2:] == (r0, r1) and all(b for _, _, b in cells[j].lines):
                    chain.append(j)
                    end = span[j][1]
            # (only below data rows: a header row of bold cells beside empty ones has the same shape,
            # 7001C / 5019A requirements matrices 'Section' | 'Description' | 'Requirement ...')
            data_above = any(cells[j].lines and span[j][3] <= r0 and not all(b for _, _, b in cells[j].lines)
                             for j in range(len(cells)))
            # ... with rows below it and no numbers in the pieces (HB-32-26A Table 9-5 ends with two bold
            # 'Global : 20.6 g RMS' | '... 12.0 g RMS' value cells)
            data_below = any(cells[j].lines and span[j][2] >= r1 for j in range(len(cells)))
            plain = not any(re.search(r"\d", cells[j].text) for j in [i, *chain])
            if len(chain) == len(others) and (not chain or (data_above and data_below and plain)) and (
                    not straddle or (data_below and plain and not chain)):
                group_cells[i] = clean_label(" ".join([c.raw, *(cells[j].raw for j in chain)]), keys)
                group_parts.update(chain)
                if straddle:
                    header_groups.add(i)

    # header rows: from the top while every text cell touching the row looks like a header
    nrows = len(ys) - 1
    header_rows = 0
    for r in range(nrows):
        touching = [i for i, c in enumerate(cells) if span[i][2] <= r < span[i][3] and c.lines and i not in foot_cells]
        if any(i in group_cells and i not in header_groups for i in touching):
            break
        touching = [i for i in touching if i not in header_groups]
        if r == 0 or (touching and all(header_like(cells[i]) for i in touching)):
            header_rows = r + 1
        else:
            break
    header_bottom = ys[header_rows]
    header = [i for i, c in enumerate(cells) if c.bottom <= header_bottom + 0.5 and i not in header_groups]
    body = [i for i, c in enumerate(cells) if c.top >= header_bottom - 0.5 and i not in foot_cells
            and i not in group_cells and i not in group_parts]

    # column names from the header cells covering each fine column
    names = []
    for col in range(ncols):
        path = []
        for i in sorted(header, key=lambda i: cells[i].top):
            c0, c1, _, _ = span[i]
            if c0 <= col < c1 and cells[i].text and cells[i].text not in path:
                path.append(cells[i].text)
        names.append(" / ".join(path))
    groups: list[tuple[str, list[int]]] = []
    for col, name in enumerate(names):
        if groups and (groups[-1][0] == name or not name):
            groups[-1][1].append(col)
        else:
            groups.append((name or f"col{col}", [col]))

    # a header cell spanning several fine columns that each carry their own body cells in at least two
    # rows heads unlabelled sub-columns: 'Sums' -> 'Sums (1)', 'Sums (2)'
    def own_body(col: int) -> int:
        return sum(1 for i in body if cells[i].lines and span[i][0] == col and span[i][1] == col + 1)

    split_groups: list[tuple[str, list[int]]] = []
    for name, cols in groups:
        head = any(cells[i].text and span[i][0] <= cols[0] and span[i][1] >= cols[-1] + 1 and span[i][1] - span[i][0] >= 2
                   for i in header)
        if len(cols) >= 2 and head and all(own_body(c) >= 2 for c in cols):
            split_groups += [(f"{name} ({n})", [c]) for n, c in enumerate(cols, 1)]
        else:
            split_groups.append((name, cols))
    groups = split_groups

    def cells_in(cols: list[int]) -> list[int]:
        return [i for i in body if span[i][0] <= cols[-1] and span[i][1] > cols[0]]

    # value columns: any numeric cell, or (after the first column) no body text at all, like the
    # first metal column of a triangular compatibility matrix whose only cell is the black diagonal
    numeric_groups = [k for k, g in enumerate(groups) if any(numeric(cells[i]) for i in cells_in(g[1]))]

    # a first column 'No' / '#' / 'Item' holding only bare row numbers (or nothing, on a page that only
    # carries the end of a row) labels the rows together with the column after it ('No' | 'Test'); the
    # rest are values even where no line starts with a number (10-03C 'Levels')
    row_number = False
    if len(groups) >= 3 and ROW_NUMBER_HEAD_RE.match(groups[0][0]):
        texts = [normalise(cells[i].text) for i in cells_in(groups[0][1]) if cells[i].lines and i not in foot_cells]
        row_number = all(ROW_NUMBER_RE.match(t) for t in texts)
        if row_number:
            numeric_groups = [k for k in numeric_groups if k > 0]

    def bold_header(cols: list[int]) -> bool:
        hs = [i for i in header if cells[i].lines and span[i][0] <= cols[-1] and span[i][1] > cols[0]]
        return bool(hs) and all(all(b for _, _, b in cells[i].lines) for i in hs)

    def empty_column(k: int, cols: list[int]) -> bool:
        """No body text, except in cells that also span into the value columns to its right (a shaded
        empty 'FOSY'-style column under a bold header)."""
        texts = [i for i in cells_in(cols) if cells[i].lines and i not in foot_cells]
        if not texts:
            return True
        reach = [n for n in numeric_groups if n > k]
        spans_in = [i for i in texts if span[i][1] > cols[-1] + 1 and reach and span[i][1] > groups[reach[0]][1][0]]
        return len(spans_in) == len(texts) and bold_header(cols)

    value_groups = [g for k, g in enumerate(groups) if k in numeric_groups or (k > 0 and empty_column(k, g[1]))]
    first_value = 2 if row_number else groups.index(value_groups[0]) if value_groups else 1
    label_groups, val_groups = groups[:first_value], groups[first_value:]

    # a wrapped table repeats one column pattern side by side ('m | s | m | s ...', no label column):
    # unfold it into value columns P and the blocks' rows one after the other
    blocks = 1
    nv = len(val_groups)
    if not label_groups:
        for p in range(2, nv // 2 + 1):
            if nv % p == 0 and [n for n, _ in val_groups] == [n for n, _ in val_groups[:p]] * (nv // p):
                blocks = nv // p
                break
    block_len = nv // blocks

    def unique(gs: list[tuple[str, list[int]]]) -> list[tuple[str, list[int]]]:
        seen: dict[str, int] = {}
        out = []
        for name, cols in gs:
            seen[name] = seen.get(name, 0) + 1
            out.append((name if seen[name] == 1 else f"{name} ({seen[name]})", cols))
        return out

    label_groups = unique(label_groups)
    names_final = [n for n, _ in unique(val_groups[:block_len])]
    if blocks == 1:
        val_groups = unique(val_groups)
    else:
        val_groups = [(names_final[k % block_len], cols) for k, (_, cols) in enumerate(val_groups)]

    # Logical rows: the ruled grid rows, each split further when a value cell inside that
    # single grid row stacks several values ('1,25' over '1,1' for Launch / On Orbit).
    value_cells = {i for _, cols in val_groups for i in cells_in(cols)}
    foot_top = min((cells[i].top for i in foot_cells), default=ys[-1])
    anchors: list[float] = []
    centres: list[float] = []  # anchors standing for a grid row without a value line of its own
    for r in range(header_rows, nrows):
        lo, hi = ys[r], ys[r + 1]
        if lo >= foot_top - 0.5:
            break
        own = [i for i in range(len(cells)) if span[i][2] == r and span[i][3] == r + 1 and i not in foot_cells
               and i not in group_cells and i not in group_parts]
        # value cells of different columns stacking values at shared y's: sub-rows; the anchors are
        # the value lines only (wrapped label lines never make anchors)
        vstacks = [[y for t, y, _ in cells[i].lines if VALUE_TOKEN_RE.match(t)] for i in own if i in value_cells]
        vstacks = [v for v in vstacks if len(v) >= 2]
        sub = _cluster([y for v in vstacks for y in v], 3.0)
        shared = [y for y in sub if sum(any(abs(y - y2) <= 3 for y2 in v) for v in vstacks) >= 2]
        if len(vstacks) >= 2 and len(shared) >= 2:
            anchors += sub
            continue
        per_cell = [[y for t, y, _ in cells[i].lines if VALUE_TOKEN_RE.match(t)] for i in own if i in value_cells]
        stacked = [y for v in per_cell if len(v) >= 2 for y in v]
        no_stack = not stacked
        # stacked values are sub-rows only when a label in the same grid row names them
        # ('Launch' / 'On Orbit' beside '1,4' / '1,5'); 32-10 Table 4-4 prints '1,4' three times
        # in one man-rated cell with no sub-row labels: that is one row
        label_ys = [y for i in own if i not in value_cells for _, y, _ in cells[i].lines]
        if stacked and sum(any(abs(y - s) <= 3 for y in label_ys) for s in _cluster(stacked, 6.0)) < 2:
            per_cell = [v for v in per_cell if len(v) < 2]
            stacked = []
        vals = stacked or [y for v in per_cell for y in v]  # a lone value beside a stack spans the stack
        if vals and no_stack:
            anchors.append(min(vals))  # lone values at different heights: still one logical row
        elif vals:
            anchors += _cluster(vals, 6.0)
        elif any(cells[i].lines for i in own):
            anchors.append((lo + hi) / 2)
            centres.append(anchors[-1])
        # else: an empty grid row (sub-cell borders only); spanning cells cover it
    # a value cell stacking several values over several grid rows defines the rows it covers
    for i in value_cells:
        vals = [y for t, y, _ in cells[i].lines if VALUE_TOKEN_RE.match(t)]
        if len(vals) >= 2 and span[i][3] - span[i][2] > 1:
            c = cells[i]
            anchors = [a for a in anchors if not (a in centres and c.top <= a <= c.bottom)] + vals
    # a row whose cells all span several fine grid rows gets no anchor above (Q-ST-70C Table 5-1:
    # the black diagonal cells add grid lines that split 'Nickel ...'); give it one
    for i in sorted((i for i in body if cells[i].lines), key=lambda i: i not in value_cells):
        c = cells[i]
        if c.top >= foot_top - 0.5 or any(c.top - 0.5 <= a <= c.bottom + 0.5 for a in anchors):
            continue
        vals = [y for t, y, _ in c.lines if VALUE_TOKEN_RE.match(t)]
        anchors.append(vals[0] if vals else (c.top + c.bottom) / 2)
    anchors = _cluster(anchors, 3.0)
    seg_cache: dict[int, dict[float, str] | None] = {}
    label_cells = {i for _, cols in label_groups for i in cells_in(cols)}
    for i in label_cells:
        listed = _list_labels(cells[i], [a for a in anchors if cells[i].top - 0.5 <= a <= cells[i].bottom + 0.5],
                              [cells[j] for j in label_cells if j != i])
        if listed:
            seg_cache[i] = listed

    spanned: set[tuple[int, float]] = set()
    grey = _grey_rects(page, tbl.bbox)  # shaded cells (H19); empty for tables without grey fills
    anchors_sorted = sorted(anchors)

    def shaded_at(cols: list[int], a: float) -> bool:
        boxes = [cells[i].bbox for i in cells_in(cols) if cells[i].top - 0.5 <= a <= cells[i].bottom + 0.5]
        if not boxes:
            return False
        k = anchors_sorted.index(a)
        top = min(b[1] for b in boxes)
        bottom = max(b[3] for b in boxes)
        if k > 0:
            top = max(top, (anchors_sorted[k - 1] + a) / 2)
        if k + 1 < len(anchors_sorted):
            bottom = min(bottom, (a + anchors_sorted[k + 1]) / 2)
        return _covered((min(b[0] for b in boxes), top, max(b[2] for b in boxes), bottom), grey) >= 0.5

    def text_at(cols: list[int], a: float, name: int = -1) -> str:
        parts = []
        for i in cells_in(cols):
            c = cells[i]
            if not (c.top - 0.5 <= a <= c.bottom + 0.5) or not c.lines:
                continue
            if i not in seg_cache:
                seg_cache[i] = _segment(c, anchors, is_value=i in value_cells)
            seg = seg_cache[i]
            t = c.raw if seg is None else seg.get(a, "")
            if seg is None and sum(c.top - 0.5 <= x <= c.bottom + 0.5 for x in anchors) > 1:
                spanned.add((name, a))
            if t:  # each cell is visited once: equal text of two different cells is kept twice
                parts.append(t)
        return " ".join(parts)

    rows = []
    numbered = any(NUMBERED_GROUP_RE.match(t) for t in group_cells.values())
    current: tuple[float, str] | None = None  # the latest one-row group: (anchor, text)
    for b in range(blocks):  # an unfolded wrapped table: block 1's rows, then block 2's, ...
        block = val_groups[b * block_len:(b + 1) * block_len]
        for a in anchors:
            labels = {name: clean_label(text_at(cols, a), keys) for name, cols in label_groups}
            vals = {}
            for name, cols in block:
                cell = parse_cell(text_at(cols, a, cols[0]), keys)
                cell.spans_rows = (cols[0], a) in spanned and bool(cell.text)
                cell.shaded = bool(grey) and shaded_at(cols, a)
                vals[name] = cell
            if not any(v.text for v in vals.values()) and not any(labels.values()):
                continue
            if group_cells:
                if numbered:
                    # a bold '4. Widget leak' label beside its values is a one-row group of its own
                    # (no label columns, 10-03C Table 4-1: the label sits in the first column)
                    own_group = next((clean_label(cells[i].raw, keys) for i in (label_cells or cells_in(block[0][1]))
                                      if cells[i].lines and cells[i].lines[0][2]
                                      and cells[i].top - 0.5 <= a <= cells[i].bottom + 0.5
                                      and NUMBERED_GROUP_RE.match(normalise(cells[i].text))), None)
                    if own_group:
                        labels = {k: "" for k in labels}
                        current = (a, own_group)
                above = [(cells[i].top, t) for i, t in group_cells.items() if cells[i].top < a]
                if current and (not above or current[0] > max(above)[0]):
                    group = current[1]
                else:
                    group = max(above)[1] if above else ""
                labels = {"Group": group, **labels}
            rows.append(TableRow(labels, vals))
    val_groups = val_groups[:block_len]

    units = {}
    for name, _ in label_groups + val_groups:
        m = re.search(r"\(([^()]*(?:Pa|psi|N|kg|m|s|Hz|g|°C|K|%)[^()]*)\)\s*$", name)
        if m:
            units[name] = m.group(1)

    return Table(
        doc_id=doc_id,
        issue=issue,
        table_id=table_id,
        caption=caption,
        label_columns=(['Group'] if group_cells else []) + [n for n, _ in label_groups],
        value_columns=[n for n, _ in val_groups],
        rows=rows,
        footnotes=footnotes,
        units=units,
        page=page_no,
    )


def _notes_first(c: _CellText) -> bool:
    return bool(c.lines) and bool(NOTES_FIRST_RE.match(c.lines[0][0]))


def _parse_notes(lines: list[str], footnotes: dict[str, str]) -> None:
    """Turn the lines of a notes cell into footnotes: '(1) ...' / '1 ...' -> '1', 'a ...' / '* ...' as
    printed, legend entries 'R=Required' / 'R - ...' -> 'Key R', 'NOTE 1 ...' -> 'NOTE 1'; under a
    'NOTES:' / 'Assumptions:' heading a 'label 1: text' line is footnotes['label 1'] and other lines are
    joined into footnotes['NOTES']."""
    legend_mode = bool(LEGEND_START_RE.match(lines[0])) and not NOTE_LINE_RE.match(lines[0])
    key: str | None = None
    heading: str | None = None
    heading_lines: list[str] = []

    def flush() -> None:
        if heading and heading_lines:
            footnotes[heading] = " ".join(heading_lines)

    for text in lines:
        if re.fullmatch(r"(?:Key|Legend)\s*:?", text, re.I):
            key = None
            continue
        if NOTES_HEADING_RE.match(text):
            flush()
            heading, heading_lines, key = text[:-1], [], None
            continue
        if m := NOTE_LINE_RE.match(text):
            key = m.group(1)
            footnotes[key] = m.group(2)
        elif legend_mode and (m := LEGEND_LINE_RE.match(text)):
            key = f"Key {m.group(1)}"
            footnotes[key] = m.group(2)
        elif m := PAREN_NOTE_RE.match(text):
            key = m.group(1)
            footnotes[key] = m.group(2)
        elif LEGEND_ENTRY_RE.match(text):
            for part in LEGEND_SPLIT_RE.split(text):
                pm = LEGEND_ENTRY_RE.match(part)
                if pm:
                    key = f"Key {pm.group(1)}"
                    footnotes[key] = pm.group(2)
        elif not heading and (m := LETTER_NOTE_RE.match(text)) and (key is None or _next_marker(key) == m.group(1)):
            key = m.group(1)
            footnotes[key] = m.group(2)
        elif not heading and (m := DIGIT_NOTE_RE.match(text)) and (key is None or not key.isdigit() or int(key) + 1 == int(m.group(1))):
            key = m.group(1)
            footnotes[key] = m.group(2)
        elif heading and (m := LABELLED_NOTE_RE.match(text)):
            key = m.group(1)
            footnotes[key] = m.group(2)
        elif heading and key is None:
            heading_lines.append(text)
        elif key:
            footnotes[key] += " " + text
    flush()


def _next_marker(key: str) -> str:
    if key.startswith("*"):
        return key + "*"
    if len(key) != 1 or not key.isalpha():
        return ""
    return chr(ord(key) + 1)


# --------------------------------------------------------------------------- shaded cells (H19)

SHADE_MIN, SHADE_MAX = 0.5, 0.95  # grey fills in this range mark a cell; black rules and white fills do not


def _grey_level(color) -> float | None:
    if isinstance(color, (int, float)):
        color = (color,)
    if not color or not all(isinstance(v, (int, float)) for v in color):
        return None
    if len(color) == 1 or (len(color) == 3 and max(color) - min(color) < 1e-3):
        return float(color[0]) if SHADE_MIN <= color[0] <= SHADE_MAX else None
    return None


def _grey_rects(page, bbox=None) -> list[tuple[float, float, float, float]]:
    """(x0, top, x1, bottom) of the grey-filled rectangles on the page (inside `bbox` if given)."""
    out = []
    for r in page.rects:
        if not r.get("fill") or _grey_level(r.get("non_stroking_color")) is None:
            continue
        if bbox and not (r["x0"] >= bbox[0] - 1 and r["x1"] <= bbox[2] + 1 and r["top"] >= bbox[1] - 1
                         and r["bottom"] <= bbox[3] + 1):
            continue
        out.append((r["x0"], r["top"], r["x1"], r["bottom"]))
    return out


def _covered(region: tuple[float, float, float, float], rects: list[tuple[float, float, float, float]]) -> float:
    """Fraction of `region` (x0, top, x1, bottom) covered by the union of `rects`."""
    x0, t, x1, b = region
    area = (x1 - x0) * (b - t)
    if area <= 0:
        return 0.0
    clipped = [(max(r[0], x0), max(r[1], t), min(r[2], x1), min(r[3], b)) for r in rects]
    clipped = [r for r in clipped if r[2] > r[0] and r[3] > r[1]]
    if not clipped:
        return 0.0
    xs = sorted({v for r in clipped for v in (r[0], r[2])})
    total = 0.0
    for xa, xb in zip(xs, xs[1:]):
        spans = sorted((r[1], r[3]) for r in clipped if r[0] <= xa and r[2] >= xb)
        cur_end = None
        for ta, tb in spans:
            if cur_end is None or ta > cur_end:
                total += (xb - xa) * (tb - ta)
                cur_end = tb
            elif tb > cur_end:
                total += (xb - xa) * (tb - cur_end)
                cur_end = tb
    return total / area


MARKER_RE = re.compile(r"^(?:>|\d{1,2})$")
NOTE_MARKER_RE = re.compile(r"^(>|\d{1,2})(?!\d)\s*(.*)$")


def shading_legend(page, table: Table, bbox, lines: list[Line]) -> None:
    """If the table has shaded cells: read the swatch legend printed below it ('[grey box] Required Test.'
    plus '> ...', '1 ...' note lines with a bold marker) into table.footnotes and blank the consumed lines.
    Then mark the legend's markers in the cells (apply_markers)."""
    if not any(c.shaded for r in table.rows for c in r.cells.values()):
        return
    swatches = [r for r in _grey_rects(page)
                if -1 <= r[1] - bbox[3] <= 30 and r[0] >= bbox[0] - 1 and r[2] - r[0] < 60 and r[3] - r[1] < 15]
    for sw in sorted(swatches, key=lambda r: (r[1], r[0])):
        head = next((ln for ln in lines if ln.text and sw[1] - 3 <= ln.top <= sw[3]
                     and 0 <= ln.x0 - sw[2] <= 6), None)
        if head is None:
            continue
        table.footnotes["shaded"] = head.text
        head.text = ""
        last_bottom, key = head.bottom, None
        for ln in sorted((ln for ln in lines if ln.text and ln.top > head.top), key=lambda ln: ln.top):
            if ln.top - last_bottom >= 8:
                break
            m = NOTE_MARKER_RE.match(ln.text)
            if abs(ln.x0 - sw[0]) <= 2 and ln.first_bold and m:
                key = m.group(1)
                table.footnotes[key] = m.group(2)
            elif key and ln.x0 > sw[0] + 2:
                table.footnotes[key] += " " + ln.text
            else:
                break
            last_bottom = ln.bottom
            ln.text = ""
        break
    apply_markers(table)


def apply_markers(table: Table) -> None:
    """Legend markers inside value cells ('1', '2,3', '2 >', '2 <454 kg') become Cell.footnotes."""
    keys = {k for k in table.footnotes if MARKER_RE.match(k)}
    if not keys:
        return
    for row in table.rows:
        for cell in row.cells.values():
            toks = [t for t in re.split(r"[ ,]+", cell.text) if t]
            if re.fullmatch(r"\d+,\d{2,}", cell.text) and not all(t in keys for t in toks):
                continue  # a decimal comma ('1,25'), not two markers ('2,3' is markers)
            marks = [t for t in dict.fromkeys(toks) if t in keys and t not in cell.footnotes]
            if not marks:
                continue
            cell.footnotes.extend(marks)
            if toks[0] in keys:
                cell.value = None


# --------------------------------------------------------------------------- continuation, duplicates


def header_signature(table: Table) -> tuple[str, ...]:
    """Normalised column names of a table: equal for a table and its repeated-header continuation."""
    # the synthetic 'Group' column is left out: a page without a group-heading row has none
    names = [c for k, c in enumerate(table.label_columns) if not (k == 0 and c == "Group")] + table.value_columns
    return tuple(" ".join(c.lower().split()) for c in names)


def is_page_top(table_top: float, line_tops: list[float], page_height: float) -> bool:
    """True when a table sits right under the running header: no body text above it on the page."""
    band = 0.1 * page_height
    return table_top < 0.2 * page_height and all(t < band for t in line_tops if t < table_top)


def trailing_caption(lines: list[Line], page_height: float) -> tuple[Line, str] | None:
    """A caption that is the last text on the page (footer excluded): its table is on the next page."""
    body = sorted((ln for ln in lines if ln.text and ln.top < 0.88 * page_height), key=lambda ln: ln.top)
    for k in range(len(body) - 1, max(-1, len(body) - 4), -1):  # caption plus up to two wrapped lines
        if CAPTION_RE.match(body[k].text):
            tail = body[k:]
            if all(b.top - a.bottom < 0.8 * a.size for a, b in zip(tail, tail[1:])):  # wrapped title lines only
                return body[k], " ".join(x.text for x in tail)
    return None


def continues(open_table: Table | None, open_page: int | None, cand: Table, page_no: int) -> bool:
    """A caption-less table at the top of the next page repeating the open table's header continues it."""
    return (open_table is not None and open_page == page_no - 1
            and header_signature(open_table) == header_signature(cand))


def _align_columns(base: Table, cont: Table) -> None:
    """A continuation page can split label and value columns differently from the first page (10-03C
    Table 6-1 p. 89: an empty column there turns 'Reference clause' into a label). The headers are the
    same (`continues`), so re-key its rows to the base's columns by position."""
    own = lambda t: [k for k in t.label_columns if k != "Group"]  # noqa: E731
    bk, ck = own(base) + base.value_columns, own(cont) + cont.value_columns
    if (own(base), base.value_columns) == (own(cont), cont.value_columns) or len(bk) != len(ck):
        return
    keys = set(base.footnotes) | set(cont.footnotes)
    for r in cont.rows:
        src = [r.labels.get(k, "") if k in r.labels else r.cells.get(k, Cell("")) for k in ck]
        labels = {"Group": r.labels.get("Group", "")} if "Group" in base.label_columns else {}
        cells = {}
        for k, v in zip(bk, src):
            if k in base.value_columns:
                cells[k] = v if isinstance(v, Cell) else parse_cell(v, keys)
            else:
                labels[k] = v.text if isinstance(v, Cell) else v
        r.labels, r.cells = labels, cells
    cont.label_columns, cont.value_columns = list(base.label_columns), list(base.value_columns)


def merge_continuation(base: Table, cont: Table, page_no: int) -> None:
    """Append the continuation's rows to `base` (rows remember their page); footnotes are merged."""
    _align_columns(base, cont)
    last_group = next((r.labels["Group"] for r in reversed(base.rows) if r.labels.get("Group")), "")
    rest = list(cont.rows)
    # leading rows with every label cell empty are the end of the base's last row, carried over the break
    label_keys = [k for k in cont.label_columns if k != "Group"]
    if base.rows and label_keys:
        keys = set(base.footnotes) | set(cont.footnotes)
        last = base.rows[-1]
        # ... and an empty first value cell: 5019A's continuation rows also have empty labels (the label
        # column is printed on the first page only) but start with their own clause number
        while rest and all(rest[0].labels.get(k) == "" for k in label_keys) and not _first_value(rest[0]):
            r = rest.pop(0)
            for k, cell in r.cells.items():
                if cell.text and k in last.cells:
                    old = last.cells[k]
                    last.cells[k] = parse_cell(f"{old.text} {cell.text}".strip(), keys)
                    last.cells[k].spans_rows = old.spans_rows
    for r in rest:
        r.page = page_no
        if "Group" in r.labels and not r.labels["Group"]:
            r.labels["Group"] = last_group  # no heading yet on the new page: still under the previous one
        elif r.labels.get("Group"):
            last_group = r.labels["Group"]
        base.rows.append(r)
    for k, v in cont.footnotes.items():
        base.footnotes.setdefault(k, v)


def _first_value(row: TableRow) -> str:
    return next(iter(row.cells.values())).text if row.cells else ""


def _caption_words(caption: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", caption.lower()))


def is_degenerate(table: Table) -> bool:
    """A box without inner rules parsed as rows that are all alike: every row repeats the same text, or
    (5020B Table 8, an appendix example: 12 rows of 105-126 characters) the same first 80 characters."""
    if len(table.rows) < 3:
        return False
    texts = [" ".join([*r.labels.values(), *(c.text for c in r.cells.values())]) for r in table.rows]
    if len(set(texts)) == 1:
        return True
    # the shared-prefix test only for the box shape (no label columns, one value column): a long 'Group'
    # label repeats on every row of a requirements matrix (5019A Tables 4-7, 5002B Table 1)
    return (not table.label_columns and len(table.value_columns) == 1
            and len(os.path.commonprefix(texts)) >= 80)


def dedupe_tables(tables: list[Table]) -> list[Table]:
    """Table IDs are unique per document: a repeated ID (an Appendix A requirements-matrix copy) is
    dropped in favour of the first, unless its caption is clearly a different one (word overlap < 0.5)."""
    first: dict[str, Table] = {}
    out = []
    for t in tables:
        prev = first.get(t.table_id)
        if prev is None:
            first[t.table_id] = t
            out.append(t)
            continue
        a, b = _caption_words(prev.caption), _caption_words(t.caption)
        if a and b and len(a & b) / len(a | b) < 0.5:
            out.append(t)  # genuinely different table under the same number: keep, report in the health check
    return out


# --------------------------------------------------------------------------- boxed one-column tables (H16 T4)


def _merge_spans(spans: list[tuple[float, float]], gap: float = 2.0) -> list[tuple[float, float]]:
    out: list[list[float]] = []
    for a, b in sorted(spans):
        if out and a - out[-1][1] < gap:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def _rules(page) -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]:
    """Merged rules of a page, drawn as lines or as thin filled rectangles (touching segments joined):
    horizontal (y, x0, x1) and vertical (x, top, bottom)."""
    hs: list[tuple[float, float, float]] = []
    vs: list[tuple[float, float, float]] = []
    for o in list(page.lines) + list(page.rects):
        w, h = o["x1"] - o["x0"], o["bottom"] - o["top"]
        if h < 2 and w >= 2:
            hs.append(((o["top"] + o["bottom"]) / 2, o["x0"], o["x1"]))
        elif w < 2 and h >= 2:
            vs.append(((o["x0"] + o["x1"]) / 2, o["top"], o["bottom"]))

    def merge(items):
        out = []
        for key in _cluster([k for k, _, _ in items], 1.5):
            group = [(a, b) for k, a, b in items if abs(k - key) <= 1.5]
            out += [(key, a, b) for a, b in _merge_spans(group)]
        return out

    return merge(hs), merge(vs)


def find_box(page, cap_bottom: float, text_lines: list[Line]) -> tuple[float, float, float, float] | None:
    """A box of four rules (top and bottom of the same x-range >= 100 pt, a vertical at each end) whose top
    edge lies within 30 pt below `cap_bottom` and which holds at least two text lines."""
    hs, vs = _rules(page)
    for y0, xa, xb in sorted(hs):
        if not (cap_bottom - 2 <= y0 <= cap_bottom + 30) or xb - xa < 100:
            continue
        for y1, xc, xd in sorted(hs):
            if y1 <= y0 + 5 or abs(xc - xa) > 2 or abs(xd - xb) > 2:
                continue
            if not all(any(abs(x - e) <= 2 and t <= y0 + 2 and b >= y1 - 2 for x, t, b in vs) for e in (xa, xb)):
                continue
            inside = [ln for ln in text_lines if ln.text and ln.top >= y0 - 1 and ln.bottom <= y1 + 1
                      and xa - 1 <= ln.x0 <= xb]
            if len(inside) >= 2:
                return (xa, y0, xb, y1)
    return None


def box_table(box: tuple[float, float, float, float], text_lines: list[Line], table_id: str, caption: str,
              doc_id: str, issue: str, page_no: int) -> Table:
    """One 'Entry' column, one row per text line inside the box; the lines leave the text flow."""
    rows = []
    for ln in sorted(text_lines, key=lambda ln: ln.top):
        if ln.text and ln.top >= box[1] - 1 and ln.bottom <= box[3] + 1 and box[0] - 1 <= ln.x0 <= box[2]:
            rows.append(TableRow(labels={}, cells={"Entry": parse_cell(ln.text, set())}))
            ln.text = ""
    return Table(doc_id=doc_id, issue=issue, table_id=table_id, caption=caption, label_columns=[],
                 value_columns=["Entry"], rows=rows, page=page_no)


# --------------------------------------------------------------------------- pages


@dataclass
class PdfContent:
    lines: list[Line]
    tables: list[Table]
    table_lines: dict[int, str]  # index of caption line in `lines` -> table_id


def read_pdf(path: Path, doc_id: str = "", issue: str = "") -> PdfContent:
    import pdfplumber

    pages: list[list[Line]] = []
    tables: list[Table] = []
    captions: list[tuple[int, float, str, Table]] = []  # (page, top, table_id, table) to tag caption lines
    open_table: Table | None = None  # last table of the previous page, which the next page may continue
    open_page: int | None = None
    pending: tuple[int, float, str] | None = None  # (page, top, text) of a caption ending the previous page
    with pdfplumber.open(str(path)) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            found = [t for t in page.find_tables() if len(t.rows) >= 2 and t.bbox[2] - t.bbox[0] > 100]
            boxes = [t.bbox for t in found]

            def outside(obj, boxes=boxes):
                if obj.get("object_type") != "char":
                    return True
                cx, cy = (obj["x0"] + obj["x1"]) / 2, (obj["top"] + obj["bottom"]) / 2
                return not any(b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in boxes)

            flow = page.filter(outside)
            lines = []
            for tl in flow.extract_text_lines(return_chars=True):
                ln = _make_line(tl["chars"], tl["text"], pno)
                if ln:
                    lines.append(ln)
            pages.append(lines)

            used_tops: set[float] = set()
            attached: Table | None = None  # table produced by the last table found on this page
            for n, t in enumerate(found):
                attached = None
                cap_lines = [ln for ln in lines if ln.bottom <= t.bbox[1] + 1 and t.bbox[1] - ln.top < 70]
                cap = None
                for k, ln in enumerate(cap_lines):
                    if CAPTION_RE.match(ln.text):
                        cap = (ln, " ".join(x.text for x in cap_lines[k:]))
                if cap is None:
                    # no caption: only a table at the top of the page can be a continuation (H15) or
                    # the body of a caption that ended the previous page (H16a); else a figure or layout box
                    top_tbl = n == 0 and is_page_top(t.bbox[1], [ln.top for ln in lines], page.height)
                    if not top_tbl:
                        continue
                    if open_table is not None and open_page == pno - 1:
                        cont = extract_table(page, t, open_table.table_id, "", doc_id, issue, pno, open_table.footnotes)
                        if continues(open_table, open_page, cont, pno):
                            apply_markers(cont)
                            merge_continuation(open_table, cont, pno)
                            attached = open_table
                    elif pending is not None and pending[0] == pno - 1:
                        _, cap_top, cap_text = pending
                        m = CAPTION_RE.match(cap_text)
                        table_id = f"Table {m.group(1)}"
                        tbl = extract_table(page, t, table_id, m.group(2).strip(), doc_id, issue, pno)
                        tables.append(tbl)
                        captions.append((pno - 1, cap_top, table_id, tbl))
                        attached = tbl
                    continue
                m = CAPTION_RE.match(cap[1])
                table_id = f"Table {m.group(1)}"
                # footnotes printed just below the table (NASA style: '* ...', '** ...')
                extra: dict[str, str] = {}
                body_size = Counter(round(ln.size) for ln in lines).most_common(1)[0][0]
                key, last_bottom = None, t.bbox[3]
                for ln in sorted((ln for ln in lines if ln.top >= t.bbox[3] - 1), key=lambda ln: ln.top):
                    if ln.top - last_bottom > 8 or ln.size >= body_size:
                        break
                    fm = FOOTNOTE_LINE_RE.match(ln.text)
                    if fm and fm.group(1).startswith("*"):
                        key = fm.group(1)
                        extra[key] = fm.group(2)
                    elif key:
                        extra[key] += " " + ln.text
                    else:
                        break
                    last_bottom = ln.bottom
                    ln.text = ""  # consumed: keep it out of the requirement text flow
                tbl = extract_table(page, t, table_id, m.group(2).strip(), doc_id, issue, pno, extra)
                shading_legend(page, tbl, t.bbox, lines)
                tables.append(tbl)
                captions.append((pno, cap[0].top, table_id, tbl))
                used_tops.add(cap[0].top)
                attached = tbl
            # a caption with no table below it may head a box without inner rules (one-column table)
            for k, ln in enumerate(lines):
                if not ln.text or not CAPTION_RE.match(ln.text) or ln.top in used_tops:
                    continue
                if any(t.bbox[1] >= ln.bottom - 1 and t.bbox[1] - ln.top < 70 for t in found):
                    continue
                tail = [ln]  # wrapped caption lines
                for nxt in lines[k + 1:]:
                    if nxt.text and nxt.top - tail[-1].bottom < 0.8 * tail[-1].size and not CAPTION_RE.match(nxt.text):
                        tail.append(nxt)
                    else:
                        break
                box = None
                for n in range(1, len(tail) + 1):  # shortest caption first: box lines can sit right under it
                    box = find_box(page, tail[n - 1].bottom, lines)
                    if box is not None:
                        tail = tail[:n]
                        break
                if box is None or any(b[0] < box[2] and b[2] > box[0] and b[1] < box[3] and b[3] > box[1] for b in boxes):
                    continue
                m = CAPTION_RE.match(" ".join(x.text for x in tail))
                table_id = f"Table {m.group(1)}"
                tbl = box_table(box, lines, table_id, m.group(2).strip(), doc_id, issue, pno)
                tables.append(tbl)
                captions.append((pno, ln.top, table_id, tbl))
                used_tops.add(ln.top)
            # state for the next page: the last table (if any) may continue; a trailing caption awaits its body
            open_table, open_page = attached, pno
            tc = trailing_caption(lines, page.height)
            pending = (pno, tc[0].top, tc[1]) if tc and tc[0].top not in used_tops else None

    for t in tables:  # grey fills without a legend saying what they mean are not reported (H19)
        if "shaded" not in t.footnotes:
            for r in t.rows:
                for c in r.cells.values():
                    c.shaded = False
    keep = {id(t) for t in dedupe_tables([t for t in tables if not is_degenerate(t)])}
    tables = [t for t in tables if id(t) in keep]
    captions = [(p, top, tid) for p, top, tid, tb in captions if id(tb) in keep]

    lines = _strip_furniture(pages)
    table_lines = {}
    for i, ln in enumerate(lines):
        for pno, top, tid in captions:
            if ln.page == pno and abs(ln.top - top) < 0.5:
                table_lines[i] = tid
    return PdfContent(lines, tables, table_lines)


def _strip_furniture(pages: list[list[Line]]) -> list[Line]:
    """Drop running headers/footers: lines in the top/bottom band that repeat on many pages."""
    if not pages:
        return []
    heights = []
    for p in pages:
        if p:
            heights.append(max(ln.bottom for ln in p))
    page_h = max(heights) if heights else 800

    def band(ln: Line) -> bool:
        return ln.top < 0.1 * page_h or ln.top > 0.88 * page_h

    def key(ln: Line) -> str:
        return re.sub(r"\d+", "#", ln.text.lower())

    counts = Counter()
    for p in pages:
        counts.update({key(ln) for ln in p if band(ln)})
    repeated = {k for k, n in counts.items() if n >= max(3, 0.3 * len(pages))}
    out = []
    for p in pages:
        for ln in p:
            if not ln.text:
                continue
            if band(ln) and (key(ln) in repeated or re.fullmatch(r"#", key(ln))):
                continue
            out.append(ln)
    return out
