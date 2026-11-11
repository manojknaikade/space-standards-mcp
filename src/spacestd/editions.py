"""Edition date of a document, and issue words in a name ("Rev.1", "w/Change 3").

A citation names a document and its issue, but 7 in 10 documents are the first issue of their letter and have
an empty `issue`: the date is then the only thing that tells one edition from the next. The date is read from
the file name (ECSS downloads carry it: `...C-Rev.2(30April2025).pdf`), else from the first page (the latest
date printed there: for a NASA standard that is the approval, change or revalidation date of the copy in hand;
an NPR's 'Effective Date'; never an expiration date).
"""

from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path

log = logging.getLogger(__name__)

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]
_MON = r"(?P<mon>[A-Za-z]{3,9})\.?"
_YEAR = r"(?P<y>(?:19|20)\d{2})"
DATE_RES = [
    re.compile(rf"(?<!\d)(?P<d>\d{{1,2}})[\s-]*{_MON}[\s-]*{_YEAR}(?!\d)"),  # 30April2025, 31 July 2008
    re.compile(rf"\b{_MON}\s+(?P<d>\d{{1,2}}),?\s+{_YEAR}(?!\d)"),  # July 31, 2008
    re.compile(rf"(?<!\d){_YEAR}[-_](?P<m>\d{{1,2}})[-_](?P<d>\d{{1,2}})(?!\d)"),  # 2022-10-24, 2025-6-9
    re.compile(rf"(?<!\d)(?P<m>\d{{1,2}})[/-](?P<d>\d{{1,2}})[/-]{_YEAR}(?!\d)"),  # 03/13/2026 (US order)
]


def find_dates(text: str) -> list[date]:
    """Every date in `text`, in the order printed, in the forms covers and file names use; invalid ones are
    skipped."""
    out = []
    for rx in DATE_RES:
        for m in rx.finditer(text or ""):
            g = m.groupdict()
            if g.get("m"):
                month = int(g["m"])
            else:
                key = g["mon"].lower()
                month = next((i for i, name in enumerate(MONTHS, 1)
                              if len(key) >= 3 and (name.startswith(key) or key.startswith(name[:3]))), 0)
            try:
                out.append((m.start(), date(int(g["y"]), month, int(g["d"]))))
            except ValueError:
                continue
    return [d for _, d in sorted(out)]


def issue_date(path: Path, manifest_date: str = "") -> str:
    """ISO date of the edition in `path`: the last date in the file name, else the latest date on the first
    page of a PDF, else `manifest_date`; "" when none is found."""
    named = find_dates(Path(path).stem)
    if named:
        return named[-1].isoformat()
    if Path(path).suffix.lower() == ".pdf":
        try:
            import pdfplumber

            with pdfplumber.open(str(path)) as pdf:
                cover = pdf.pages[0].extract_text() or ""
        except Exception:
            log.debug("cannot read the first page of %s", path, exc_info=True)
            cover = ""
        # an expiration date is not the edition's date; an 'Effective Date' (NPRs) is
        cover = re.sub(r"(?i)expir\w*(?: date)?\s*:?\s*[^\n]{0,24}", " ", cover)
        effective = re.search(r"(?i)effective date\s*:?\s*([^\n]{0,24})", cover)
        printed = find_dates(effective.group(1)) if effective else []
        printed = printed or find_dates(cover)
        if printed:
            return max(printed).isoformat()
    return manifest_date or ""


# issue words after a document name: "Rev.1", "Revision F", "w/Change 3", "Change 3", "Corr.1", "Corrigendum 1"
ISSUE_WORD_RE = re.compile(
    r"[\s,(_-]*(?:(?P<rev>REV(?:ISION)?)[.\s_-]*(?P<revn>\d+|[A-Z])(?![A-Z0-9])"
    r"|(?:W[/-]?\s*|WITH\s+)?(?P<chg>CHANGE)[\s_-]*(?P<chgn>\d+)"
    r"|(?P<corr>CORR(?:IGENDUM)?)[.\s_-]*(?P<corrn>\d+))\)?", re.I)


def issue_words(text: str) -> dict[str, str]:
    """Issue words at the start of `text` (what follows a document name), or anywhere in an issue string:
    'Rev.2 Corr.1' -> {'rev': '2', 'corr': '1'}; ' w/Change 4, section 5' -> {'change': '4'}."""
    out: dict[str, str] = {}
    pos = 0
    while m := ISSUE_WORD_RE.match(text, pos):
        if m["rev"]:
            out["rev"] = m["revn"].upper()
        elif m["chg"]:
            out["change"] = m["chgn"]
        else:
            out["corr"] = m["corrn"]
        pos = m.end()
    return out


def issue_differs(asked: dict[str, str], loaded_issue: str) -> bool:
    """A named issue contradicts the loaded one when any word it states differs ('Rev.1' against 'Rev.2',
    'Rev.1' against a first issue). 'Rev.2' does not contradict 'Rev.2 Corr.1'."""
    have = issue_words(loaded_issue)
    return any(have.get(k) != v for k, v in asked.items())
