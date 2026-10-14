# Parsing notes from real documents

First pass on 5 Oct 2026 with ECSS-E-ST-32-01C Rev.2 (.docx), ECSS-E-ST-32-08C Rev.1 (.doc) and NASA-STD-5001B w/Change 3 (PDF). The v0 parser found **0 requirements** in both ECSS files. Findings, in order of impact:

## ECSS (.docx / .doc)

1. **Clause numbers and requirement letters are Word auto-numbering**, not text. python-docx returns "Strength", not "4.2.1 Strength", and no "a." markers. LibreOffice text export (`soffice --convert-to txt`) renders the numbering.
2. **Tracked changes are present** (32-01: 836 deletions, 1367 insertions; 32-08: 70 / 185). python-docx silently drops inserted text; LibreOffice export merges deleted and inserted text. Fix: accept all changes in the XML first (drop `w:del`/`w:moveFrom`, unwrap `w:ins`/`w:moveTo`, drop `*Change` property records), then export.
3. **Requirement letters run on through the whole document** in the rendered list ("r.", "aa.", "aaa."…). The ECSS ID is clause + letter restarting at a, b, c in each clause, so letters must be recomputed per clause. Checked against the 32-08 change log (4.1a, 4.2.11a, 4.6.3b–c, 4.6.4h, 4.6.5e, 4.7b all land correctly).
4. **Requirements in 32-01 carry a unique machine ID** paragraph before them, e.g. `ECSS-E-ST-32-01_0810025` (340 IDs; figures and tables have them too, so the count is 8 higher than the 332 requirement records). Use it as a stable key and parsing check where present. **32-08 (2014) has none**, so the parser cannot rely on it.
5. **Cross-reference fields are stale**: references render as "1.1.1g", "1.1.1.11" instead of the real clause. Resolve via the field's bookmark target, or flag the reference as unresolved — never cite "1.1.1g".
6. **Deleted requirements stay as placeholders** (`<<deleted>>`). Keep them as records with `kind: deleted` so lookups explain the gap instead of saying "not found".
7. **Notes and list items mis-styled in the source** (e.g. 32-08 4.5.2a: some list items formatted as NOTE). Keep verbatim; flag in eval rather than "fix".
8. `.doc` (32-08) converts cleanly to .docx with LibreOffice.

Result of the scratch pipeline (accept changes → LibreOffice text → per-clause letters): 332 requirement records in 32-01 (incl. deleted placeholders), 77 in 32-08.

## ECSS-E-ST-32C Rev.1 (PDF, 134 pages, 15 Nov 2008)

- Still the active issue on ecss.nl (checked 5 Oct 2026).
- **No machine IDs** (pre-2009 format, like 32-08), so parse checks rely on clause structure and "shall" counts (737 "shall" occurrences).
- Clause numbers and per-clause letters render correctly in the PDF. Requirements use nested lists: letter `a.` → number `1.` → `(a)` (e.g. 4.2.5c lists launch load events down to `2.(n)`). Sub-items belong to their parent requirement record, not separate requirements.
- Uses non-ASCII hyphens in IDs ("ECSS‐E‐ST‐32C", U+2010): normalise hyphens before matching references.

## NASA-STD-5019A w/Change 4 (PDF, 120 pages, revalidated 2025-09-05)

Different granularity from 5001B:

1. Only **26 top-level `[FCR n]` requirements**, but 145 tag occurrences. Most occurrences are **references inside text** ("…to satisfy requirement [FCR 11] section 7.2.a…"), not definitions. A tag is a definition only when it starts a requirement paragraph; otherwise it is a cross-reference.
2. The citable unit is finer than the FCR: e.g. FCR 11 covers sections 7.2.a–e, each with lettered items "a through k". Record ID = `FCR 11 / 7.2.a.3` style (FCR + section + item), with the FCR kept as parent.
3. Appendix A compliance matrix repeats all 26 FCRs (body/appendix split needed, as in 5001B).
4. Guidance is italic (section 1.2.5), as in 5001B.
5. Lists nest three deep: `a.` → `(1)` → `A.` (→ `i.`/`ii.`). Italic guidance paragraphs often sit *inside* a list; the items after them still belong to the requirement. Lettered items are mostly at x = 108, but some sections (6.2.5) set them at x = 90, so only `i.`/`v.`/`x.` use indentation to tell roman numerals from letters.

## NASA-STD-5001B (PDF)

1. Requirements are tagged **`[FSR n]`** (61 total) — the generic bracket-tag parser fits. Some tags are preceded by list letters "a. [FSR 7]" and section numbers "4.5.2 [FSR 53]".
2. **Every FSR appears twice**: in the body and in Appendix A (compliance matrix). Parse the body only; stop at "REQUIREMENTS COMPLIANCE MATRIX" (or use the appendix only to cross-check the count).
3. **Guidance is italic text** (section 1.2.5), lost in plain text extraction. Needed for `kind`: use a layout-aware extractor (pdfplumber font flags) to separate requirement from guidance.
4. **Page furniture** repeats on every page ("APPROVED FOR PUBLIC RELEASE…", "n of 36", document header) and must be stripped; it splits requirements across pages.
5. **Factor tables** (Tables 1–7) come out as aligned text with multi-line cells and footnote markers (`1.0*`, `N/A or 1.05**`). Table extraction must keep footnotes attached to cells.

## ECSS PDF vs Word — decision

Tested with ECSS-E-ST-32-10C Rev.2 (PDF, 27 pages):

| Issue | Word (.docx/.doc) | PDF |
| --- | --- | --- |
| Clause numbers | missing (auto-numbering) | present in text |
| Requirement letters | missing / run on (aa, aaa…) | correct, restart at a. per clause |
| Tracked changes | 800+ in 32-01, must be accepted in XML | final text only |
| Machine IDs (`ECSS-…_0110020`) | present in 32-01 | present (33 in 32-10) |
| Simple tables (Table 4-3) | explicit cell structure | clean with pdfplumber |
| Complex tables (Table 4-4, merged sub-rows) | explicit cell structure | sub-rows scrambled |
| Page furniture | none | headers, footers, page numbers to strip |
| Cross-references | stale fields ("1.1.1g") | rendered as printed (to verify) |

**Decision: PDF is the primary source for ECSS requirement text and IDs.** Use the .docx, when available, only to cross-check complex tables. Every factor table gets a hand-checked test fixture of expected cell values (values only, not text), because merged cells are where a wrong number would come from.

### Cross-check: ECSS-E-ST-32-01C Rev.2, Word vs PDF (105 pages, via Google Drive)

- Same 340 machine IDs in both; 331 requirement records matched by machine ID.
- Text start identical for every requirement where both scripts agreed on the ID → the PDF contains the accepted (final) text, no tracked-change residue.
- 22 ID disagreements, all caused by scratch-script heading detection, not by the documents. Heading patterns the PDF loader must handle:
  - chapter headings split over two lines ("9" then "Material selection") → requirements are 9a, 9b…
  - a single space after the number ("10.2 Nonconformances")
  - five-level clauses ("10.5.2.2.1")
- All 23 evaluation IDs on 32-01 resolve identically in both versions.
- `documents/` now holds both 32-01 files; the PDF loader must prefer the PDF when both exist.

## Phase 1 loader — implemented 5 Oct 2026

Code: `pdf_extract.py` (layout lines, furniture, tables), `ecss_parser.py`, `nasa_parser.py`, `word_extract.py`, dispatch and cache in `loaders.py`. Tests: `tests/test_parsers.py` (invented input), `tests/test_real_documents.py` (skipped without `documents/`).

| Document | Source | Records | Check |
| --- | --- | --- | --- |
| ECSS-E-ST-32C Rev.1 | PDF | 750 (715 requirement, 26 recommendation, 9 permission) | no machine IDs; one letter printed twice in the source (I.2.1<9.1>a) |
| ECSS-E-ST-32-01C Rev.2 | PDF | 332 (243 requirement, 21 permission, 1 recommendation, 1 guidance, 66 deleted) | 340 machine IDs = 331 on requirements + 1 table + 8 figures/deleted items |
| ECSS-E-ST-32-10C Rev.2 Corr.1 | PDF | 28 requirements, 6 tables | 35 machine IDs = 28 requirements + 6 tables + Figure 4-1 (Rev.2: 33, two requirements without) |
| ECSS-E-ST-32-08C Rev.1 | Word (.docx) | 77 (74 requirement, 1 recommendation, 2 deleted) | change-log IDs land on records |
| NASA-STD-5001B w/Change 3 | PDF | 61 FSR + 56 guidance, 7 tables | FSR 1–61, body only |
| NASA-STD-5019A w/Change 4 | PDF | 238 requirement (26 FCR + 212 FCR items/lead-ins) + 253 guidance, 8 tables | FCR 1–26, no unparsed paragraphs |

New findings while building it:

### ECSS PDFs

- **Heading detection by font, not by regex alone.** Clause headings are bold Arial 12–22 pt; body text is Palatino 10 pt. Five-level clauses in 32-01 (`10.5.2.2.1`, `10.7.2.1.1`) are *non-bold* Arial 11 pt, so the rule is "larger than body and in the heading font". The chapter number is a separate 22 pt line followed by the title.
- **Captions are bold and larger too** ("Table 4-3: …"): they must be handled before heading detection or they become headings.
- **DRD annexes** (ECSS-E-ST-32 Annexes A–Q) number their content `<5.2> Modelling assumption` in bold Palatino 11 pt. Requirement IDs there follow ECSS practice: `A.2.1<5.2>a`.
- **Not every requirement has a machine ID**: 32-10 4.3.2.1e and 4.3.2.2b have none. Machine-ID counts are a check, not a key.
- **Figure text** (Figure 4-1/4-2 in 32-10) is drawn in other fonts/sizes; boxed figures are detected by pdfplumber as tables without a "Table" caption and are dropped from the text flow.
- **List markers inside sentences**: "at least four" + "(4) times" — a line starting with a list marker starts a new item only after a complete line (ending `:`, `;`, `.`, `or`, `and`).
- **`kind`**: shall → requirement, should → recommendation, may / need not → permission (added; ECSS nomenclature treats it as normative, so it is neither a requirement nor guidance), informative annex → guidance, `<<deleted…>>` → deleted.
- ECSS-E-ST-32 nomenclature clause has a second "a." after "d." (chapter 3); chapters 1–3 are skipped anyway.

### NASA PDFs

- **Tag definition rule**: a tag defines a requirement only if it opens a paragraph *after a complete line* and its sentence contains "shall". "…to meet requirement" + newline + "[FCR 21]." is a reference. With this, 5019A has exactly 26 definitions.
- **FCR lists continue across guidance**: FCR 9 has items a–c, an italic note, then d–e. Lettered items continuing the FCR's own letter sequence are appended to the FCR record.
- **FCR item IDs**: `FCR 11 / 7.2.1.c` = FCR, implementing section, item letter. The section's non-italic lead-in ("…are to comply with … to meet requirement [FCR 11] section 7.2.a") is its own record `FCR 11 / 7.2.1`. Subsections inherit the FCR of the nearest ancestor section that names one. Roman-numeral (`i.`, `v.`) and capital-letter (`A.`) sub-items, indented deeper, stay inside the item.
- **`[Rationale: …]`** (italic) is attached to the requirement as a note; other italic paragraphs are `guidance` records with positional IDs `4.2.1 guidance 1` (section + order; not an official ID, and the citation says so by its form).
- **Table footnotes print below the table** (`*`, `**`) in 5001B, outside the ruled box; they are attached to the table and removed from the text flow.
- Wrapped section headings ("4.2.5 Pressurized Structures, … and Habitable" / "Modules") are merged.

### Tables

- Extracted from the ruled grid (pdfplumber cell boxes), not from text alignment. Each logical row is a grid row, split further where a value cell stacks several values (32-10 Table 4-3 "Man-rated S/C — Launch / On Orbit", Table 4-2 storage loads, Table 4-5 "Launch vehicle — Global / Local").
- **Merged cells**: a single value in a cell spanning several rows applies to all of them and is flagged `spans_rows` (e.g. 32-10 Table 4-2 KA 1,2 for man-rated launch and on-orbit loads; Table 4-3 man-rated metallic "FOSY verification by analysis only" 1,25 d, printed level with "Launch" but in a merged cell — read the footnote before quoting it for on-orbit).
- **Table 4-4** (joints and inserts): three sub-rows per vehicle (failure / gapping-sliding safety critical / gapping-sliding other), listed once in *one* label cell that spans all vehicle bands. A label cell whose `- item` lines divide evenly over the bands of the next label column is split per sub-row ("Joints and inserts: a - Failure", …). Man-rated S/C prints '1,4' three times in one FOSU cell: stacked values split a grid row only when a label in the same grid row is aligned with them ('Launch' / 'On Orbit'), so that is one row with text "1,4 1,4 1,4" (Rev.2; Corr.1 prints the value once). 11 rows; hand-checked against the rendered page (`tests/test_real_documents.py`).
- **ECSS-Q-ST-70C Table 5-1** (bimetallic couples, page 33): caption without separator ("Table 5-1 Compatible…"); column headers turned 90° (read per x column, bottom to top); triangular matrix whose first metal column is blank (a column with no body text after the first is a value column); the black diagonal cells add grid lines, so a row whose cells all span several fine grid rows still gets an anchor. The closing "Key:" block becomes footnotes `Key 0`–`Key 3`; a closing "NOTE 1 …" block (Q-70 Table 4-1, 32-01 Table 8-1) becomes `NOTE n` footnotes instead of a body row.
- Cell text is kept verbatim (decimal comma in ECSS, `N/A or 1.05**`), except that a word set as a subscript is spaced off (`1,25 corrected b`; one-letter subscripts stay: `Jp`); `value` is parsed only when the cell is a plain number; footnote markers are split off only when the table defines them.
- Units: these factor tables are dimensionless; a column unit is recorded only when the header states one.
- Not done: tables continued over a page (none in the current set), figures, 5019A tables (extracted, not hand-checked).

### Word path (ECSS-E-ST-32-08C)

- Same ECSS parser fed with LibreOffice-rendered paragraphs (indentation stands in for x position, numbered lines become headings); letters recomputed per clause; 77 records as in the scratch pipeline.
- Stale cross-reference fields (`1.1.1g`, `1.1.1.11`) are not resolved yet; they are kept verbatim in the text, removed from `references`, and reported in the record's `flags`.

### Performance

Parsing all six documents takes about 40 s (table detection on every PDF page). Parsed documents are cached in `documents/.spacestd-cache/`, keyed by file size/mtime, sidecar and a hash of the parser code.

## Health report on all 284 documents — 9 Oct 2026 (A2)

`python -m spacestd.health documents --corpus all --no-cache`: 33 min, 0 parse errors; 7 verified, 129 checked,
148 unchecked (numbers per document in `eval/CORPUS_HEALTH.md`). The failures fall into a few patterns. Each
one below is described with invented text so a worker can reproduce it in `tests/fixtures/`.

### H1 · ECSS level-4 headings whose number is not in the text layer (duplicate IDs)

32 ECSS documents have `(duplicate N)` IDs, 1,786 records in all. They cause most "valid IDs < 95 %" results
(e.g. E-ST-50-11C 47 %, E-ST-10-03C 61 %, E-ST-20-08C 88 %, Q-ST-70-60C 90 %, E-HB-10-02A 45 %). Example
checked on the PDF (E-ST-50-11C, page 56): under clause `5.3.5` the parser sees the letters `a`…`g`, then `a`…`e`,
then `a`…`e` again, and gives every repeat the ID `5.3.5x (duplicate N)`. Between the runs there is a level-4
heading (Arial 11 pt, body text is Times 10 pt). Its number (`5.3.5.2`) is **not** in the text layer: one blank
character stands at the number's position. A NOTE in the text refers to the clause by that number, so the
number exists in the document.

Invented reproduction (PDF-like line stream, the heading has no number):

```
5.3.5 Widget control words            <- level-3 heading, number present
a. The widget shall …
b. The widget shall …
Start-of-widget word                   <- heading font, no number in the text layer
a. The start word shall …
b. The start word shall …
```

Fix idea: when a heading-font line without a number is followed by a letter list that restarts at `a.`, number
it as the next child of the current clause (`5.3.5.1`, `5.3.5.2`, …) and flag the clause path as inferred
(`flags: ["inferred clause number"]`). If the first unnumbered heading comes after lettered items of the parent
clause, the count still starts at `.1`. A NOTE that names the clause can confirm the inferred number.

*Done (A2a, 9 Oct): `ecss_parser.unnumbered_heading` takes a heading-font line (or bold heading) without a
number, wrapped lines merged, as a heading when the next line (machine IDs aside) is an `a.` item at the item
indent. It is numbered as the next free child at the depth its style has shown on numbered headings (a numbered
`5.3.6.1` in the same style makes the next one `5.3.6.2`), else as the next child of the last numbered clause;
its records carry `flags: ["inferred clause number"]`. An annex heading resets the count until the annex has a
numbered clause. Wrapped non-bold numbered headings now merge their second line (it could otherwise look like an
unnumbered heading). Not checked on the real 32 documents; the NOTE cross-check is not implemented.*

### H2 · NASA requirements that are lettered list items without a tag (unparsed share)

47 NASA documents have more than 10 % unparsed text; in the 8719.x and 8739.x series it is 83–100 %. The NASA
parser keys on bracketed tags (`[FSR 24]`, `nasa_parser.TAG_RE`). Older standards have no tags: their
requirements are numbered (`1.`, `(1)`) or lettered (`a.`) items under a numbered section, and they end up as
unparsed fragments. NASA-STD-3001 Vol 2 uses tags of the form `[V2 nnnn]`: the prefix contains a digit, which the
tag pattern does not allow.

Fragment starts over the 47 documents (≈ 17,900 fragments): plain paragraph ≈ 6,100 (mostly handbooks; A5),
numbered item `1.` ≈ 3,500, lettered item `a.` / `A.` ≈ 3,400, `(1)` ≈ 620, `[V2 nnnn]` tag 465 (3001 Vol 2 only),
`Word N` ≈ 330, bullet ≈ 220, other ≈ 1,450.

Invented reproduction:

```
4.2 Widget handling
a. The operator shall ground the widget before handling.
b. Widgets shall be stored in a dry container.
4.3 Gizmo checks
1. Each gizmo shall be inspected before use.
(1) The inspection shall be logged.
4.4 Gadget logs [V7 1234] Each gadget shall have a log.
```

Fix idea: in a NASA document with few or no tags, make each lettered or numbered item containing "shall" (and each
"shall" paragraph of a numbered section) a requirement with ID `<section>.<letter>` (e.g. `4.2.a`) or
`<section> shall N`. `health.NASA_REQ_RE` then needs a tagless branch. In `nasa_parser.TAG_RE`,
`LEAD_TAG_RE` and `CONTEXT_RE`, accept a tag prefix with a digit (`[A-Z]{1,5}\d?`, for `V2 6001`).

*Done (A2a, 9 Oct): tag prefixes may end in a digit (`[A-Z]{2,6}` or `[A-Z]{1,5}\d`), and a section
number with a short heading may precede a lead tag (`4.4 Gadget logs [V7 1234] …`). A body with no tag
definitions at all is **tagless**: there `1.` also opens a paragraph, and every lettered, numbered or plain
paragraph containing "shall" that no tag owns becomes a requirement: `4.2a` (section + letter, the ECSS-like form
the citation gate already reads), `4.3(1)` (`1.` or `(1)`), or `4.4 req N` (the N-th "shall" paragraph of the
section). A lead-in ending in `:` keeps the lettered list below it; `(1)` under a numbered item stays in it.
Items without "shall" stay unparsed. Documents with even one tag definition keep the tagged rules unchanged,
so the verified 5001B / 5019A grouping does not move. `health.NASA_REQ_RE` and the citation gate know the new
forms (`4.3(1)` only where a loaded document uses it). Not yet checked on the real PDFs: re-run A2 📄 and
spot-check 8719.x / 8739.x, 5005D, 7001C, 7009B and 3001 Vol 2.*

*Checked on the real PDFs (A2 re-run, 9 Oct, local):* 17 NASA standards move to `checked` (e.g. 5005D unparsed
297 → 4, 5018 286 → 13, 7009B 82 → 1); sampled `4.4.3b`, `5.7.1c` (5018) and `5.2.8b` (5005D) sit at the right
clause and letter on the PDF page. Still `unchecked`: 8719.x / 8739.x (unparsed 12–73 %), 3001 Vol 2 (21 %).
7001C comes out `checked` but with the wrong IDs: see H5.

### H5 · NASA lead tag after a dotted paragraph number (tagged body read as tagless)

NASA-STD-7001C numbers each requirement paragraph and puts its tag after the number *with a trailing dot*:
65 lines of the form `<n.n.n.n>. [TAG n]`, 64 distinct tags. `nasa_parser.LEAD_TAG_RE` accepts a section number
before a tag only without the dot (`4.4 [TAG n]`, `4.4 Title [TAG n]`), so no body line counts as a tag
definition, the body is treated as tagless (H2), and 51 of 54 requirements get positional IDs
(`4.4.1 req 3`) whose text starts with the real tag; only 3 get `TAG n / section`. Before H2 those 51 paragraphs
were unparsed (82 records, 3 requirements). Wave-1 document, so it matters for B3.

Invented reproduction:

```
4.3 Widget tests
4.3.1 Shaking
4.3.1.1. [WTR 5] Each widget shall be shaken before delivery.
4.3.1.2. [WTR 6] The shaking level shall be logged.
4.3.2 Spinning
4.3.2.1. [WTR 7] Spin tests shall use a balanced fixture.
```

Expected: `WTR 5`, `WTR 6`, `WTR 7` (section 4.3.1 / 4.3.2 as context), document not tagless. Fix idea: allow an
optional `.` after the section number in `LEAD_TAG_RE` (`(?P<sec>\d+(?:\.\d+)+)\.?\s+`), and check that
`SECTION_RE` does not take such a line as a heading first. Also seen while sampling: in 5005D an unbolded
subsection heading (`6.3.1.4.4` + title) lands as the text of a guidance record.

*Fixed 9 Oct (A2a): `LEAD_TAG_RE` takes an optional `.` after the section number; the reproduction
above is `tests/test_parsers.py::test_nasa_lead_tag_after_dotted_paragraph_number` (clause `4.3.1.1`, heading path
through `4.3.1`). Not yet checked on the real 7001C (A2 re-run 📄). The 5005D heading case is still open.*

### H3 · Health check: file name and cover ID compared too strictly

27 documents are flagged "file name names another standard"; all 27 are false positives (12 fail on this alone).
The file name names the same standard in a shorter or different form:

| File-name form (invented numbers) | Catalogue ID |
| --- | --- |
| `NASA-STD-1234 - 2022-07-15-NASA-STD-1234A-Approved.pdf` | `NASA-STD-1234A` |
| `ECSS-E-ST-12-34 Rev.1(31May2022).pdf` | `ECSS-E-ST-12-34C` |
| `nasa-std-87991a.pdf` (dot dropped) | `NASA-STD-8799.1A` |
| `NASA-STD-1234Ver-40.pdf` | `NASA-STD-1234` |

Fix (`health.name_check`): compare the base number only (family, type, number; ignore the revision letter, the
missing dot and case), or reuse the catalogue's own dotless-name matching. `differs` should mean a different
base number.

*Done (A2a, 9 Oct): `health.base_number` drops case, dots and a revision letter at the end of the number
or part; a different number, or a different part, still `differs`.*

### H4 · Threshold notes for `THRESHOLDS`

- `min_records: 3` is too low: 15 documents are `checked` with fewer than 20 records (e.g. Q-ST-70-61C with 3,
  E-HB-32-20 Parts 1A/2A with 7). Suggest 20 for standards; handbooks wait for A5 (section records).
- The 8 ECSS adoption notices (`-AS-`) have 0–1 records by nature. Report them as `adoption notice`, not
  `unchecked`, or exclude them from `--corpus all`.
- 11 documents fail only on ragged tables (one ragged table in 1–7). A share threshold punishes documents with
  few tables; consider "ragged tables ≤ 10 % or ≤ 1".
- Zero-record standards worth a look on the PDF: ECSS-M-70A (old layout), ECSS-Q-ST-60-13C Rev.2,
  NASA-STD-2818, -2821, -3001 Vol 1, -6030, -6033, -8719.17/.24/.28. ECSS-S-ST-00-01C is the glossary (0 is right).
- ECSS-Q-ST-60C Rev.4: 5 records, all with IDs like `4.2.3.4no` (a table's yes/no column read as letters).

*Done (A2a, 9 Oct): `min_records` 20 for standards, 3 for handbooks and other types (until A5); ragged tables
fail only when more than 1 and more than 10 %; adoption notices get the single reason `adoption notice` (tier
stays `unchecked`: nothing in them is parsed or checked). The zero-record standards and the Q-ST-60C Rev.4 IDs
stay open (local, on the PDF).*

## Wave-1 health report — 9 Oct 2026 (B1)

`python -m spacestd.health documents --corpus loaded --no-cache` with the wave-1 patterns in
`documents/corpus.yaml`, parser with H1 and A4 merged (42 documents, 9 min; per-document numbers in
`eval/CORPUS_HEALTH_WAVE1.md`): 7 verified, 24 checked, 11 unchecked, 0 errors. Against the A2 report:
NASA-STD-7001C confirms H5 on the real PDF (64 `PVTR n` records instead of `4.4.x req N`, unparsed 7 → 1), and
ECSS-E-ST-10-03C confirms H1 (valid IDs 61 % → 99 %, duplicates 184 → 5, now `checked`). Two wave-1 handbooks
keep duplicate IDs for other reasons: E-HB-32-24A (88 %, 32 duplicates) is H7; E-HB-32-26A (62 %,
16 duplicates) has prose paragraphs between lettered lists that restart at `a.` under one clause with no heading
in between (e.g. clause 16.3), which is handbook prose, not requirements: A5 territory, not a parser bug.
NASA-HDBK-5010 (baseline w/Change 1) is superseded by 5010A Vol 1 (its cover says so) and was moved to
`documents/superseded/`; it had parsed to 0 records, for the reason in H6.

### H6 · Text that becomes neither a record nor an unparsed fragment is invisible to the health check

The `Unparsed` column only counts what the NASA parser hands back. Two paths drop body text without a trace:

1. **ECSS documents never report unparsed text.** `loaders._load_pdf` sets `doc.unparsed` only on the NASA path;
   `parse_ecss_lines` keeps lettered items and drops plain paragraphs. ECSS-E-HB-32-20 Parts 1A–8A (118–535
   pages, 37k–109k words of text layer each) give 0–23 records and 0 unparsed; Parts 1A–4A even come out
   `checked` with 7–23 records (handbook minimum is 3). E-HB-32-21A (461 pages) gives 1 record, E-HB-32-22A 2.
2. **A NASA document without a bold `4 Title` heading returns `[], []`.** `parse_nasa_lines` looks for the
   first section-4 heading as the body start and gives up silently when there is none (NASA-HDBK-5010
   baseline: 235 pages, 6,747 lines, 0 records, 0 unparsed).

Invented reproduction (ECSS-like line stream; same idea for NASA with no section-4 heading):

```
4 Widget design guidance               <- level-1 heading
4.1 General                            <- level-2 heading
Widgets are usually sized from the     <- plain body paragraphs, no a./b. items
worst-case spin load, and margins are
often reported per load case.
4.2 Margins
A margin table is commonly kept per
widget assembly.
```

Today: 0 records, 0 unparsed, and with a handbook ID the document needs only 3 records to be `checked`.
Expected: the health report sees the dropped text. Fix ideas (with fixtures): (a) the ECSS parser
returns plain body paragraphs as unparsed fragments, like the NASA parser; (b) `parse_nasa_lines` reports
"no body start" (or falls back to the first numbered section) instead of `[], []`; (c) the health report adds a
coverage measure (words in records + unparsed ÷ body words of the text layer) with a threshold, so a long
document with a handful of records cannot be `checked`. A5 (section records for handbooks) is the real fix for
the handbook bodies; (c) keeps the tier honest until then.

*Done (B2, 9 Oct): all three. (a) `parse_ecss_lines(..., stats=)` returns body paragraphs that become no
record (chapters ≥ 4 and annexes, figure text in another font or size left out) as unparsed fragments
`<clause>: <first 120 chars>`, split at a vertical gap (each Word paragraph is one); the loader puts them in
`Document.unparsed` for PDF and Word. (b) The NASA body starts at a bold `4 Title` or `4.0 Title`, else at the
first bold numbered heading, else at the first line, so a document without section 4 gives records or
unparsed fragments, never `[], []`. (c) Both parsers count the words of the body lines (`Document.body_words`)
and of the uncut unparsed paragraphs; the health report's coverage is (words in record texts and notes +
unparsed words) ÷ body words, shown as a column, and a measured document below `min_coverage` (50 %, a first
guess) is `unchecked`. Tests: `test_ecss_prose_paragraphs_are_unparsed_h6`,
`test_nasa_body_without_section_4_heading_h6`, `test_coverage_keeps_a_long_document_with_few_records_unchecked`.
Not checked on the real documents: ECSS standards with a prose-only principles chapter may now exceed the 10 %
unparsed share (fragments are counted per paragraph); re-run the wave-1 health report and tune
`min_coverage` / the share before trusting tier changes.*

*A5, 10 Oct (round 1): handbooks no longer leave their prose unparsed. ECSS `-HB-` and NASA-HDBK bodies give one
`guidance` record per numbered section; prose that resumes after a list, table or NOTE joins the section's record
(without that, E-HB-32-25A had 416 `(duplicate n)` IDs). Wave-1 re-run: E-HB-32-20 Parts 1A–7A and -21A, -23A–-26A
`checked`, 0 unparsed. Thresholds re-tuned on the same run: `min_coverage` 75 % (standards 78–99 %), and the
unparsed share no longer gates ECSS standards, whose descriptive paragraphs are fragments by design.*

### H8 · Wave-1 handbooks still `unchecked` after A5 (10 Oct, not investigated)

From `eval/CORPUS_HEALTH_WAVE1.md`: NASA-HDBK-7005 gives 40 guidance records with IDs the NASA family does not
accept (valid IDs 0 %) and 1,763 unparsed fragments (98 %): its body is probably not reached by the
section-record path (no numbered section before the prose, or a heading style the NASA parser does not take).
E-HB-32-20 Part 8A gives 0 records and 0 body words (the text layer may be empty: check for a scanned PDF).
E-HB-32-26A keeps 16 duplicates from lettered prose lists. NASA-HDBK-5010 Vol 1 has 64 duplicate IDs. Needs the
real PDFs (🧠📄) before a fixture can be written.

*Fixed for E-HB-32-20 Part 8A (B3, 10 Oct, fixture only): a handbook with no chapter >= 4 (and no annex) takes
chapters 1 onwards as body. In a chapter whose title contains "Glossary", each `Term: definition` line that starts
a paragraph (vertical gap, or the previous line ended with `.`, `;` or `?`) starts a `guidance` record with ID
`<clause>:<Term>` and the flag `glossary term`; following paragraphs join it, newline-separated. Letter-group
headings (`A`, `B`) end the record and are no clauses. `health.GLOSSARY_ID_RE` makes these IDs valid. Not run on the
real PDF: the assumed layout (terms in body text, colon after the term) is from the orchestrator's measurements.*

*Fixed for NASA-HDBK-7005 (B3-fix-NASA, 10 Oct, fixtures only): in the NASA handbook path a regular-weight line `N.` / `N.N` + a title with at least 80 % upper-case letters, at the left margin (commonest x0), without dot leaders or a trailing page number, is a section heading, and the body may start at the first such heading (before section 4). Test `test_nasa_handbook_uppercase_plain_headings_h8`. The other H8 items (E-HB-32-20 Part 8A, 26A, 5010) are open.*

### H7 · ECSS numbered headings set at body size (E-HB-32-24A)

E-HB-32-24A sets level-4 headings (`12.6.4.1 Title`) in the heading font, bold, but at the body size (10 pt;
level 3 is 12 pt, level 2 16 pt). The number *is* in the text layer (unlike H1), but `parse_ecss_lines` only takes
lines at least ~1 pt above body size as headings, so every lettered list under `12.6.4.1`, `12.6.4.2`, … lands
in `12.6.4` and gets `(duplicate N)`. Some lists are also introduced by bold body-font `a. Title` lines.

Invented reproduction (sizes in pt; body font Serif 10):

```
12.6.4 Widget joints                    <- Sans-Bold 12
12.6.4.1 Bolted widgets                 <- Sans-Bold 10 (same size as body)
a. Bolt preload should be recorded.     <- Serif 10
b. Washers are usually hardened.
12.6.4.2 Bonded widgets                 <- Sans-Bold 10
a. Bond lines are often inspected.
```

Expected: `12.6.4.1a`, `12.6.4.1b`, `12.6.4.2a` (today `12.6.4a`, `12.6.4b`, `12.6.4a (duplicate 2)`). Fix idea: a
bold line in a non-body font whose leading number is a child of the current clause (one more level, next free
index) is a heading even at body size.

*Done (B2, 9 Oct): `ecss_parser.small_heading` takes a bold line in the heading font at body size (within
0.9 pt) as a heading when its number has at least two levels and is the next free child of the current clause
or of one of its parents (`12.6.4.1` under `12.6.4`, then `12.6.4.2`); a number that skips ahead stays body text.
Its wrapped second line (same font, bold, not an `a.` item) joins the title. The invented reproduction above is
`test_ecss_numbered_heading_at_body_size_h7`. The bold body-font `a. Title` lines are still read as items. Not
checked on the real E-HB-32-24A (expect its 32 duplicates to go).*

## Next parser steps

- [ ] Resolve Word cross-reference fields via bookmarks (32-08), or get 32-08 as PDF
- [x] Separate Table 4-4 sub-row labels (failure / gapping-sliding) from the joint-type label cell (hand test F2)
- [x] 5019A third-level items (`A.`, `ii.`) under `(n)`, and list items resuming after a guidance paragraph, stay with their requirement; off-indent `b.` is a letter item (hand test F1)
- [ ] Hand-check 5019A tables; table continuation across pages
- [ ] Clause path for NASA requirements numbered `(1)` under a lettered heading (5001B FSR 1–5 show clause `4`)

### H9 · Tagless NASA paragraphs merge numbered sub-paragraphs (10 Oct, B3/B5 prep)

NASA-STD-7003A numbers its requirements as paragraphs (`4.3.1`, `4.3.1.1`, `4.3.2`) with no tags, so the tagless
rule makes `4.3 req n` records, and one record can hold a paragraph and its numbered sub-paragraph (`4.3 req 1`
holds 4.3.1 and 4.3.1.1). The IDs do not match what the document prints, and they shift if a paragraph is added.
Fix idea (with an invented fixture): in tagless NASA bodies, a numbered paragraph containing "shall" becomes a
record with its own number as ID (`4.3.1.1`). Eval questions hand-18 and w1-010 cite the current IDs.

*Fixed (B3-fix-NASA, 10 Oct, fixtures only): in a tagless body a paragraph starting with a dotted number below the current heading (`4.3.1`, `4.3.1.1`) opens its own paragraph and, with "shall", becomes a requirement with that number as ID (clause = the number); `health.NASA_REQ_RE` accepts it. "should" / "may" numbered paragraphs stay unparsed, as before. Test `test_nasa_tagless_numbered_paragraphs_get_their_own_ids_h9`. Eval questions hand-18 and w1-010 still cite the old IDs.*

### H10 · Equations are lost (10 Oct)

Equations set as images or math fonts leave only their symbol lists: ECSS-E-ST-33-01C 4.7.5.3.1d/e (minimum
actuation torque and force) keep "derived by the equation: where: …" and none of the factors. No fix planned:
answers point to the PDF clause (eval hand-20 says so).

### H11 · NASA-STD-5020B separation factors (10 Oct, check in B3)

The owner reports that 5020B section 4.2.3 describes the Figure 1 logic (minimum separation factor of safety) in
text as well. The parsed records of 4.2.3 hold only the definition of a separation-critical joint and the
non-separation-critical value; no record holds the separation-critical values (one record is just the subscript
`sep`). Either that text sits in the figure's text layer (dropped as figure text) or it is lost in parsing. Check
pages 20–21 against `get_section_outline("NASA-STD-5020B", "4.2.3")` during B3.

*Checked 10 Oct (B3): the separation-critical logic and values are only in the Figure 1 flow chart (p. 20). The body
text of 4.2.3 is the tag, the definition and the non-separation-critical case, all parsed; nothing is lost from
the body. A fix would need figure text (or the answer points to the figure, as hand-19 does).*

### H12 · NASA tagged bodies: false `TAG n / section` records (10 Oct, B3)

In tagged NASA standards, any non-italic paragraph after a tag in the same section becomes a requirement record
`TAG n / section` (the rule that makes 5019A's FCR items). Outside 5019A it catches equations, footnotes, figure
labels, table notes and legends, NOTEs and sentence tails: 21 false records in 10 wave-1 standards, none with
"shall" (5022 `NCPR 9 / 4.2.1`, `NCPR 35 / 4.4.2`; 5002B `LAR 7 / 4.1.6`, `LAR 69 / 4.9.3.1`; 5008B `PCR 277 / 4.5.8`;
5009C `NER 74 / 4.5.5`; 5012C `PSER 3 / 5`, `PSER 27 / 9.5.1`; 5017B `DDMR 39 / 4.9.7`, `DDMR 60 / 4.15.1`; 5020B
`TFSR 5 / 4.3.1`, `TFSR 8 / 4.4.1`, `TFSR 9 / 4.4.2`, `TFSR 11 / 4.4.4`, `TFSR 23 / 4.7.4`, `TFSR 29 / 4.8.4`; 7001C
`PVTR 8 / 4.3.3.1`, `PVTR 12 / 4.3.3.5`, `PVTR 60 / 4.5.2`, `PVTR 62 / 4.5.4`; 7002B `PTR 1 / 4.1`). They inflate the
requirement counts and two were spot-check IDs. Two cases: a tag with "Deleted Requirement" and no "shall" (5002B LAR 7,
p. 14) should be a `deleted` record `LAR 7`; an unlettered list entry after a lettered list (5002B LAR 69, p. 27;
7001C PVTR 12 methods, p. 19) belongs in the tagged record. Fix idea (invented fixture): outside FCR-style
documents, a `TAG n / section` paragraph without shall / should / may is guidance (or is appended to the tagged
record when it continues its list); a tag line whose rest is "Deleted …" becomes `deleted`.

*Fixed (B3-fix-NASA, 10 Oct, fixtures only): outside sections that name the tag they implement ("to meet requirement [FCR 11]"), a paragraph after a tagged requirement without shall / should / may / must is no longer a `TAG n / section` record: it joins the tagged record when it follows its lettered list, else it is prose (unparsed, or the section record in handbooks). A tag whose text starts "Deleted" becomes a `deleted` record. Test `test_nasa_tagged_non_requirement_paragraphs_are_not_records_h12`. Real-PDF effect (the 21 false records) not yet measured: re-run the wave-1 health report.*

### H13 · Missed headings give wrong IDs (10 Oct, B3)

Checked on the rendered pages. (a) ECSS-E-ST-10-03C inferred level-4 numbers (H1): 12 of 68 headings are wrong
(34 records). An unnumbered heading with no requirements under it is not counted (4.3.3.1 "General", p. 29, so
parsed 4.3.3.1–4 are printed 4.3.3.2–5; 4.5.4.1 is printed 4.5.4.2, p. 38), and an unnumbered level-4 heading after
a numbered level-5 one becomes its child (parsed 6.5.1.2.3.1–4 are printed 6.5.1.3–6, pp. 111–113; 6.5.5.2.2.1–3 are
printed 6.5.5.3–5, pp. 126–127). The heading font (size), not the previous number, should set the level. (b) ECSS DRD
item headings `<n>` are missed now and then, so the next item's letters restart under the previous `<n>`: 10-03C
`A.2.1<8>a (duplicate 4)` is printed `A.2.1<9>a` (p. 134), `C.2.1<5>a (duplicate 3)` and `C.2.1<9>a (duplicate 2–4)`
are `<6>` and `<10>`–`<12>`, and the last item `C.2.1<14>` (p. 141) is unparsed. (c) NASA tagless bodies:
NASA-STD-5005D misses most level-5 headings under 6.3.1.3, 6.3.1.4 and 6.3.1.5 and the level-3 heading 6.4.14
(pp. 54–61, 68), so about 37 records carry the previous section's number (20 flagged as duplicates); some of those
headings end up as guidance text. NASA-STD-5018 misses 4.7.3 (p. 23, title with a ® sign), so 4.7.3a–b are
`4.7.2a/b (duplicate)`. A "(duplicate)" flag in an ECSS or tagless body is a sign of a missed heading, not of a
repeated ID in the source.

*Fixed (B3, 10 Oct, fixture only; not run on the real PDFs). (a) A bold heading-font line without a number that is
smaller than the numbered level-3 bold headings is level 4 by size: it takes the next free child of the current
level-3 clause whether prose, a NOTE or a list follows, and a preceding numbered level-5 heading does not make it
a child. (The `a.` list is still required for unnumbered headings of other styles, H1.) Test:
`test_ecss_unnumbered_level4_sized_by_font_h13a`. (b) Hypothesis, not checked on the PDF: the `<n>` heading was
missed because it is set at body size (bold, or heading font), where `is_heading` wanted 0.9 pt more; such a line
is now a DRD heading. Test: `test_ecss_drd_heading_at_body_size_h13b`. If 10-03C still shows `(duplicate)` under
`<n>`, the cause is something else (look at the font and size of the missed line on the page).*

*Fixed, part c (B3-fix-NASA, 10 Oct, fixtures only): (a) a non-bold italic line `N.N.N Title` at the heading margin, short, without "shall" or a final period, whose number is a child or the next sibling of the current section (or of a parent), is a heading in tagless bodies; (b) a heading that is at least 60 % bold and ends in a registered/trademark/copyright sign counts as bold. Tests `test_nasa_italic_headings_in_tagless_body_h13c`, `test_nasa_bold_heading_with_trademark_glyph_h13c`. Not checked on the 5005D / 5018 PDFs; parts a and b (ECSS) are open.*

### H14 · Lost, merged or mis-kinded requirements (10 Oct, B3)

- NASA-STD-5006A GWR 103 (first item at the top of p. 26) is in no record and not in `unparsed` (dropped with the
  page header?).
- NASA-STD-5008B: `A.`/`B.`/`C.` items that carry their own tags (PCR 179–181 p. 38, PCR 230–231 p. 43) are merged
  into PCR 178 / PCR 229, so `get_requirement("PCR 180")` fails; PCR 249 (p. 45) sits inside the guidance record
  `4.5.2.2 guidance 3`. A tag inside a list item should start its own record.
- ECSS-E-ST-32-03C: after the equation in 5.5f item 3 (p. 18), items 3–4 and requirement 5.5g are lost (not in
  `unparsed` either).
- Kind: 10-03C `6.5.7.1b` is printed `>>deleted>>` (source typo for `<<deleted>>`) and counts as a requirement;
  32-02C `4.5.1.4c` and `5.3.1a` are "can" statements (possibility in the ECSS verbal forms) and count as
  requirements.

*Fixed (B3, 10 Oct, fixture only): (1) 32-03C equation numbers (`1 1`, `2 2`, non-bold 12 pt serif at the right
margin) were read as chapter 1 / 2 headings, which ended the body. A clause-numbered line whose title is only
digits, or whose chapter is below the current one (non-bold), is no heading and is dropped as figure-font text.
(2) `>>deleted>>` is kind `deleted`; an item with "can" / "cannot" and no shall / should / may / need not is
`guidance`. NASA H14 items (5006A, 5008B) are not part of this change.*

*Fixed for NASA (B3-fix-NASA, 10 Oct, fixtures only): a tag inside a list item (`A. [TAG n] ...`; uppercase letters are now allowed in `LEAD_TAG_RE`) or in an italic block starts its own record. 5006A GWR 103: a figure caption (`Figure 4—Title`, `Table 4-1: Title`) now always opens and closes its own paragraph, so the item on the next page is no longer glued to it and dropped by the caption skip. Tests `test_nasa_tag_inside_list_item_or_guidance_block_starts_a_record_h14`, `test_nasa_figure_caption_closes_its_paragraph_h14`. Not checked on the real PDFs; the ECSS items of H14 are open.*

### H15 · Tables continued on the next page keep only the first page (10 Oct, B3)

ECSS-E-ST-10-03C Tables 4-1, 5-1 … 5-6 and 6-1 … 6-6 repeat their header row on 1–3 following pages; only the first
page is parsed (e.g. Table 5-2 loses rows 8 shock and 9 micro-vibration on p. 50, Table 6-2 loses p. 91). These are
the test-level tables at the centre of wave 1. Fix idea (invented fixture): a table at the top of the next page whose
header row equals the open table's header (or that has no caption) continues it. The same check (header repeated on
the next page) found no other wave-1 table that continues.

*Fixed (B3, fixture-tested only; re-run the health report to confirm on the real PDFs):* a caption-less table that
starts right under the running header of the next page and repeats the open table's normalised header is appended to
it (chains over several pages). Rows from continuation pages carry `page` (the table's `page` stays the first).

### H16 · Tables not extracted (10 Oct, B3)

- NASA-STD-5023 Tables 1 and 3: the caption is the last line of p. 18 / p. 43 and the table body is on the next page.
- NASA-STD-5017B Table 1 (torque margin factors, p. 21) and Table 2 (p. 25): caption and body on one page, still not
  found (no outer grid?). Table 1 is the standard's main numeric table.
- NASA-STD-7001C Table 2 (minimum workmanship random vibration spectrum, p. 18): a boxed list without cell lines;
  its last line ends up in the false record `PVTR 8 / 4.3.3.1` (H12).

*Fixed (B3, fixture-tested only):* (a) a caption that is the last text of a page takes the caption-less table at the
top of the next page (`Table.page` is the body page). (b) 5017B Tables 1–2 were not missed by pdfplumber: their
captions are `Table 1―Title` with U+2015, which `CAPTION_RE` now accepts (also U+2012). Still open: 7001C Table 2.

### H17 · Table cell defects (10 Oct, B3)

- **Footnote superscripts fused into numbers** (NASA-STD-5012C Table 1, p. 19): 1.10 with note 5 is `1.105`
  (value 1.105), 2.0 with note 8 is `2.08`, 1.50 with notes 6,7 is `1.506,7`, 1.70 with note 10 is `1.7010`. The
  values are wrong. Superscripts need the font size (smaller than the cell text) to become footnote markers.
  *Fixed (B3):* a run under 0.8 x the line's size, of digits, commas or 1–2 letters right after a digit, is marked as
  a superscript and `parse_cell` turns it into footnotes (`1.10` + `5` -> 1.10, ['5']; `6,7` -> ['6', '7']). Markers
  not among the table's footnote keys are kept as footnotes anyway. Edge: a size-reduced exponent after `10` would
  read as a footnote.
- Stacked sub-rows in one cell, `≤` lost (private-use glyph), method headings as data rows (5009C Tables 1–2).
- Appendix A requirements-matrix pages parsed as tables, with the body tables' IDs (5009C `Table 1` p. 37 and
  `Table 2` p. 39 are copies; 5012C `Table 2` p. 32 is the matrix). Matrix pages should be skipped and table IDs
  should be unique per document. *Fixed (B3):* a caption-less table never gets an ID except as a continuation or
  trailing-caption body; a repeated ID keeps the first table and drops the later one unless its caption shares less
  than half its words with the first. The cause of the duplicate IDs was not identified without the PDFs.
- Footnotes, notes and legends parsed as data rows (5020B Tables 1–4, 32-02C Table 4-5, 5008B Table 1, 5017B
  Table 5); group-heading rows absorbed into the column names (5008B Table 1, 10-03C Table 4-2).
- Rotated column headers come out reversed and letter-spaced (5017B Tables 5 and 7).
- Multi-column layouts collapsed: 5020B Table 5 keeps only the last of four m / s column pairs; 5020B Tables 7–8
  join each column into one cell; 33-01C Tables 4-6 / 4-7 merge two calculation columns (and 4-7's owner is `G`).
- Merged label cells: 32-02C Table 4-8 gives rows 1–4 all four application names as label.
- Meaning carried by shading is lost: 7002B Table 1 marks required tests by grey cells (fixed in H19).

### H19 · Shaded cells and degenerate tables (12 Oct, round 5)

- **Shading is meaning** (NASA-STD-7002B Table 1, p. 15): value cells are "required" only by a grey fill (filled
  rects, single-component grey 0.8 or 0.749, sometimes two rects per cell); rules are thin black (0.0) filled rects.
  *Fixed:* `Cell.shaded` is set when grey fills (0.5 to 0.95; black and white ignored) cover at least half of a
  body value cell's row band. The swatch legend under the table (grey box within 30 pt below, text line to its
  right) becomes `footnotes["shaded"]`; the following lines whose first character is bold and which start with `>`
  or 1-2 digits become footnotes of that marker (wrapped lines joined) and leave the text flow. Marker tokens in
  cells (`1`, `2,3`, `2 >`, `2 <454 kg`) become `Cell.footnotes`; a cell starting with a marker has no `value`
  (`text` stays verbatim). `1,25`-style decimals (a comma followed by 2+ digits) are not read as markers.
  `_row_text` appends the legend text (or "shaded") to a shaded cell, so "required test" is searchable.
  Continuation pages mark cell footnotes from the first page's legend but not shading of a legend they lack.
- **Degenerate tables** (5020B Table 8, p. 100, an appendix worked example): a box without inner rules parsed as 12
  identical rows. `read_pdf` drops a table with at least 3 rows whose labels and cell texts are all identical.

### H18 · ECSS-E-ST-10-03C tables: group rows in column 0, lone values, row numbers (12 Oct, R5-T1003)

Layouts measured on the real tables (orchestrator), fixed on invented PDFs (`tests/test_table_10_03.py`).

- **Group-heading row with empty neighbours** (Tables 4-1, 5-1, 6-1 and the other matrices): a bold label in column 0
  with empty cells (one spanning cell or one per column) in the rest of the row was read as a second header row, so
  column names became "Test / General" and the continuation pages (header without that row) never matched. Rule: a
  grid row below row 0 in which one cell has text, starts in column 0, has only bold lines and every other cell
  touching the row is empty is a group row (`Group` label column, as for a spanning heading). `header_signature` now
  leaves out the synthetic `Group` column, so a page with no group row (a notes-only continuation) still continues.
- **Lone values at different heights** (Tables 5-2, 5-4, 5-6, 6-2, 6-4, 6-6): in a ruled row where no value cell
  stacks two or more value lines, values of different columns at different heights each made a row anchor and split
  the row. Now one anchor (the topmost value line). Rows with a stack keep the old rules.
- **Row-number column, row carried over a page break**: a first column headed `No`, `No.`, `#` or `Item` whose
  non-empty body cells are all bare numbers (`12`, `3a`, `4.`) is a label column, not values; the first column with a
  value token still starts the values (the text column before it, `Test`, becomes a label as well). In
  `merge_continuation`, leading continuation rows whose label cells are all empty are the rest of the base's last row:
  their cell texts are appended (space-joined) to its cells and no row is added.
- Edges: a bold column-0 label with every other cell of its row empty is now a group row even when it is a data row
  with no values; a table whose first column is headed `Item` / `No` with bare numbers and other columns of text only
  loses the numeric first column; a continuation page starting with an unlabelled row is always read as carried.
- **Integration changes (orchestrator, round 5, after a per-table diff of all 268 tables against main):**
  - Row-number tables: `No` and the column after it are the labels, all further columns are values, also on a page
    where no line of a column starts with a number (10-03C `Levels`) or the `No` cell is empty (carried rows).
  - A carried row also needs an empty first value cell: 5019A Tables 4-7 print their label column on the first page
    only, and their continuation rows start with their own clause number (they were folded into one row).
  - `_align_columns`: a continuation page that splits label and value columns differently (an empty column there)
    is re-keyed to the first page's columns by position (10-03C Table 6-1 p. 89, 7001C Table 3 p. 32, 5019A Table 6).
  - Group rows cut into several bold cells by fine column edges (7002B `EMI` | `/EMC` | `TESTS`) are one group.
  - Numbered one-row groups (`4. ...` beside its value) are found in the first column when a table has no label
    columns (10-03C Table 4-1).
  - Key blocks under a matrix (10-03C Tables 5-1 / 5-3 / 5-5): cells of `a ...` key lines (one wide cell or several
    side by side, at least half the width from column 0), the bold heading row above and the `Key` / `R ...` legend
    cell beside them are footnotes (`a` .. `l`, `R`), not rows.
  - H19 refinements: grey fills are reported only on tables with a shading legend; a degenerate table is also one
    whose rows share their first 80 characters (5020B Table 8's tails differ).
  - Effect on other tables (reviewed on the PDFs): false sub-row splits and duplicate rows gone in 5012C Table 2,
    HDBK-5026 Table 1, HB-32-23A 5-3, HB-32-25A 12-8 / 13-5, HB-32-26A 9-9 / 13-2 / 14-4; no verified table lost a value.
  - **Regression found after #69 (B6 health showed fewer tables):** the shared-prefix degenerate test read a long
    `Group` label repeated on every row as a box and dropped ten requirements-matrix tables (5019A Tables 2, 4-7,
    5002B 1, 5012C 2, 5017B 8, 5023 4, 7001C 3); the cut-bar group rule also took matrix sub-header rows and a
    bottom row of two bold value cells (HB-32-26A 9-5) for groups. Fixed (#71): the prefix test only for a box (no
    labels, one value column); a cut bar only between data rows and without digits. The last per-table diff had been
    taken before the final integration commits: the diff now runs on the exact head, and
    `test_verified_tables_unchanged` pins the table IDs and row counts of every verified document.


### B3 follow-up on the real PDFs (10 Oct, round 3, orchestrator 📄)

Checked after the worker fixes (#46–#48) were merged; all six below have invented-fixture tests.

- H12: four `TAG n / section` records were left (5012C, 5020B, 7001C, 7002B) because a descriptive "may" or "should"
  passed the modal test. Outside FCR-style sections a `TAG n / section` record now needs "shall" or "must";
  5012C 28, 5020B 32, 7001C 64, 7002B 63 requirements, the hand-check counts.
- H13a: `level3_size` took the smallest level-3 size, and 10-03C sets its 34 term headings (`3.2.n`) as 11 pt
  level-3 headings. It is now the commonest size of the body's (chapter ≥ 4, annex) numbered level-3 headings;
  10-03C gives 4.3.3.2–5, 4.5.4.2, 6.5.1.3–6, 6.5.5.3–5 as printed.
- H13b: the 10-03C `<9>` DRD heading is 12 pt body-font bold with a bold share of 0.79 (the brackets are not bold);
  a `<n>` line now needs a bold share ≥ 0.6. The last item `C.2.1<14>` was lost because its items sit 9 pt right of
  the usual item margin (tolerance 8 → 10). 10-03C: 431 requirements, 7 permissions, 0 duplicates (hand check).
- H13c (5018 4.7.3): the number and the title are two bold lines 3 pt apart (the ® shifts the title's
  baseline); a bold number-only line and the bold line beside it are joined. 5018: 0 duplicates.
- H8 Part 8A: the glossary has no `Term:` form; terms are upper-case lines at the margin with the definition
  indented below. Rewritten to that layout: 1,645 term records (`1:<TERM>`), 3 duplicate terms.
- H8 NASA-HDBK-7005: only chapter headings were upper case; subsections (`2.2.1 Title. Prose …`, regular
  weight, title case, x0 99) are headings when the table of contents lists their number and the number is the
  plausible next section, so numbered reference lists stay text. 296 section records (was 51).

Still open: 7001C Table 2 (boxed list without cell lines), 5008B PCR count 318 vs 319 tags, 5023 Tables 1 and 3
(caption at page bottom: check after #47), E-HB-32-26A / NASA-HDBK-5010 Vol 1 duplicates, H17 notes and
multi-column table defects, ECSS-E-ST-32-11C Table 5-4 owner `D`.

### Round 4 (11 Oct 2026): H16 / H17 table fixes, NASA italic and subscript lines

Layouts measured on the PDFs first (orchestrator), then fixed by workers on invented PDFs built with
`tests/pdfgen.py` (#56–#60); each re-checked on the real tables, and the combined change compared table by table
over the 44 loaded documents (109 of 268 tables changed, all reviewed as fixes or neutral).

- Notes blocks: `(1)` / `1` markers, legends `R=…`, `R - …`, headings ending in `:` (NOTES, Assumptions), blocks
  that do not span every column -> footnotes (5020B Tables 1–4 and 7, 5017B Table 5, 32-02C Table 4-5).
- Group-heading rows (one bold full-width cell) -> a `Group` label column; numbered one-row groups; carried across
  continuation pages (5009C Tables 1–2, 5008B Table 1, 10-03C Table 4-2).
- Repeated header pattern unfolded (5020B Table 5: 40 m / s rows); unlabelled sub-columns split (33-01C 4-6 / 4-7;
  also several handbook tables that had a row of values in one cell); stacked value lines in two or more value
  columns split a ruled row, label lines never do (5020B Table 7, 26A Table 9-1, 5009C); a wrapped sub-row label
  centred on its value (32-02C Table 4-8).
- Rotated headers detected from the text matrix (pdfplumber reports them upright), word gap 0.12 × glyph width
  (5017B Tables 5 / 7; Q-70C Table 5-1 kept); Symbol-font U+F0xx mapped (≤ ≥ ± …); small digits after a letter are a
  footnote when they are a footnote key, else superscript digits (g², Zones¹).
- H16 7001C Table 2: a captioned box of thin filled rects without inner rules -> a one-column table.
- 32-11C Table 5-4: its caption directly followed Table 5-3's and was skipped as a wrapped caption line (ECSS parser).
- NASA: a partly italic line after an incomplete line does not open a paragraph (7003A 4.1.1, 5008B 319), and a
  1–2 letter line is a subscript fragment, not a paragraph or the line a list item follows (5017B DDMR 46).

Still open: 5020B Table 8 (Appendix example: box without inner rules + uncaptioned table), 7002B Table 1 (shading),
10-03C table-by-table check, appendix requirement matrices (5009C Table 3: one row).
