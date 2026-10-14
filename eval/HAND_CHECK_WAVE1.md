# Hand-check list, wave 1 (B3)

Written by `python scripts/hand_check_list.py`. Text-free: IDs, counts, pages and table shapes only.
Tick what matches the PDF; note what does not (ID and page, never the wording). Confirmed counts, IDs and
table values go into `tests/test_real_documents.py`, and the standard into `catalogue.VERIFIED`.
Standards: 19 at tier `checked` (handbooks can stay `checked`).

## Owner check, 10 Oct 2026 (done by Claude for the owner)

How it was checked (local only, nothing uploaded):

- **Counts:** the PDF text was extracted again with a different engine (pypdfium2; the parser uses pdfplumber).
  NASA tagged standards: the set of `[TAG n]` in the body pages compared with the parsed tag records. ECSS
  standards from 2019 on: the machine IDs in the PDF compared with those on records and tables. All standards:
  every "shall" sentence in the body pages looked up in the requirement records, and every requirement record
  checked for a "shall". Each miss was then looked at on the rendered page.
- **Spot checks:** record text compared word by word with the PDF page (coverage, where the record ends, kind
  against shall / should / may). Doubtful cases were checked on the rendered page.
- **Tables:** every cell value looked up in the PDF text of its page; continuation pages, tables missing from
  the parse and duplicate table IDs searched for; the tables with numbers were compared with the rendered page
  cell by cell.

`[x]` = matches the PDF. `[ ]` + ✗ = does not match (what and where). Parser findings are written up as
H12–H17 in `docs/PARSING_NOTES.md`.

| Standard | Counts | Spot checks | Tables | Ready for `VERIFIED` |
|---|---|---|---|---|
| ECSS-E-ST-10-03C Rev.1 | ✗ 431 (+1 permission) | 7/8 | 1 of 14 | no: H13 IDs, H15 tables |
| ECSS-E-ST-32-02C Rev.1 | ✗ 384 (2 "can" items) | 8/8 | 9 of 10 | after the Table 4-8 labels (H17) |
| ECSS-E-ST-32-03C | ✗ 42 (5.5g lost) | 8/8 | none | after H14 (5.5f/g) |
| ECSS-E-ST-32-11C | ✓ 119 | 8/8 | 5 of 5 | **yes** (Table 5-4 owner `D` to check) |
| ECSS-E-ST-33-01C Rev.2 | ✓ 406 | 8/8 | 5 of 7 | after Tables 4-6/4-7 (informative examples) |
| NASA-SPEC-5022 | ✗ 79 (2 false records) | 8/8 | none | after H12 |
| NASA-STD-5002B | ✗ 67 + 1 deleted | 7/8 | none | after H12 |
| NASA-STD-5005D | 251 ✓, IDs ✗ | 8/8 | none | no: H13 IDs |
| NASA-STD-5006A | ✗ 138 (GWR 103 lost) | 8/8 | none | after H14 |
| NASA-STD-5008B | ✗ 319 tags, 313 records | 8/8 | 0 of 1 | no: H14 |
| NASA-STD-5009C | ✗ 74 (1 false record) | 7/8 | 0 of 4 | no: H17 tables |
| NASA-STD-5012C | ✗ 28 (2 false records) | 8/8 | 0 of 2 | no: **Table 1 numbers wrong** (H17) |
| NASA-STD-5017B | ✗ 90 (2 false records) | 7/8 | 3 of 5, 2 missing | no: H16, H17 |
| NASA-STD-5018 w/Change 1 | 234 ✓, 2 IDs ✗ | 8/8 | 1 of 1 | after H13 (4.7.3) |
| NASA-STD-5020B | ✗ 32 (6 false records) | 6/8 | 5 of 8 | no: H12, H17 |
| NASA-STD-5023 | ✓ 105 | 8/8 | 1 of 1, 2 missing | after H16 (Tables 1 and 3) |
| NASA-STD-7001C | ✗ 64 (4 false records) | 8/8 | 1 of 1, 1 missing | after H12, H16 (Table 2) |
| NASA-STD-7002B w/Change 1 | ✗ 63 (1 false record) | 8/8 | 1 of 2 | after H12, H17 (Table 1 shading) |
| NASA-STD-7003A | ✓ 24 | 8/8 | 2 of 2 | after H9 (IDs change) |

**Round 4 re-check (11 Oct 2026, Claude for the owner, on the PDFs after #56–#61 and this PR):** 8 more standards are
`VERIFIED` with real-document tests: ECSS-E-ST-32-02C (384: the two "can" items are not requirements; Tables 4-5
and 4-8 right), ECSS-E-ST-33-01C (406; Tables 4-6 / 4-7 now two calculation columns), NASA-STD-5008B (319 = the
printed PCR tags; Table 1 groups and notes 1–2), NASA-STD-5009C (74; Tables 1–2: method groups, stacked sub-rows,
≤ / ≥), NASA-STD-5012C (28; Table 1: 15 factors match the PDF, markers 1–11 kept apart), NASA-STD-5017B (90 = the
DDMR tags; Tables 1, 2, 5, 7 right), NASA-STD-7001C (64; Table 2 found, 6 rows), NASA-STD-7003A (26: 4.1.1 back;
the 26 numbered paragraphs as printed). Still `checked`: ECSS-E-ST-10-03C (counts and IDs right; its 14 tables
need a table-by-table pass), NASA-STD-5020B (Tables 1–7 right; Table 8, the Appendix example, is not: a box
without inner rules plus an uncaptioned second table), NASA-STD-7002B (Table 1 marks required tests by shading).
Appendix requirement matrices (5009C Table 3, 5012C Table 2, 5017B Table 8, 7001C Table 3) are not relied on.

Only ECSS-E-ST-32-11C is ready for `VERIFIED` now. The others go to `VERIFIED` once the parser fixes are in and
the counts below are re-checked (the corrected counts are given per standard).

H11 (NASA-STD-5020B 4.2.3): the separation-critical values are only in the Figure 1 flow chart (p. 20). The body
text of 4.2.3 holds the tag, the definition of a separation-critical joint and the non-separation-critical case,
and no more, so nothing is lost from the body. The separation-critical values need figure text (or the PDF).

### ECSS-E-ST-10-03C Rev.1

Source: `Active ECSS Standards_PDF-files (10Oct2025)/ECSS-E-ST-10-03 Rev.1(31May2022).pdf`. Records: 466 (430 requirement, 8 recommendation, 6 permission, 10 guidance, 12 deleted).

- [ ] Requirement count 430 matches the PDF (first `4.1a` p. 23, last `C.2.1<13>c` p. 141)
  ✗ Should be 431: DRD item `C.2.1<14>` (p. 141; a and c "shall", b permission) is unparsed, and `6.5.7.1b`
  p. 127 is a deleted item printed `>>deleted>>` (source typo) but counted as a requirement. Machine IDs: 473 in the
  PDF; the 11 not on any record are those 3 DRD items, 7 tables (4-1, 5-2, 5-4, 5-6, 6-2, 6-4, 6-6 carry no machine
  ID) and Figure 5-1.
- [ ] Spot checks (ID exists, text complete, kind right): `4.1a` p. 23, `4.5.2f` p. 37, `5.5.2.2b` p. 74, `5.5.4.1j` p. 81, `6.5.1.2.3.1b` p. 111, `6.5.2.9c` p. 119, `6.5.7.3b` p. 128, `C.2.1<13>c` p. 141
  ✗ 7/8: text, page and kind right for all eight, but `6.5.1.2.3.1b` is printed 6.5.1.3b (next item).
- [ ] Parser flag "inferred clause number" on 289 records, e.g. `4.3.2.1a` p. 24, `5.5.3.1f` p. 78, `6.5.2.7d` p. 117, `6.5.7.5j` p. 131
  ✗ The four examples are right, but 12 of the 68 inferred headings are wrong (34 records, H13). The PDF prints
  4.3.3.1 (an unnumbered "General" heading with no requirements, p. 29), so parsed 4.3.3.1–4.3.3.4 are printed
  4.3.3.2–4.3.3.5 (the document's own cross-references use 4.3.3.2b, 4.3.3.3b). Parsed 4.5.4.1 is printed 4.5.4.2
  (p. 38). Parsed 6.5.1.2.3.1–4 are printed 6.5.1.3–6.5.1.6 (p. 111–113). Parsed 6.5.5.2.2.1–3 are printed
  6.5.5.3–6.5.5.5 (p. 126–127). Checked on the rendered pages; the other 56 agree with the Word file's heading
  order or the rendered page.
- [ ] Parser flag "duplicate ID" on 5 records, e.g. `A.2.1<8>a (duplicate 4)` p. 134, `C.2.1<5>a (duplicate 3)` p. 139, `C.2.1<9>a (duplicate 3)` p. 140, `C.2.1<9>a (duplicate 4)` p. 140
  ✗ Not duplicates in the source: the DRD item headings are missed (H13). `A.2.1<8>a (duplicate 4)` is printed
  `A.2.1<9>a` (p. 134); `C.2.1<5>a (duplicate 3)` and `C.2.1<9>a (duplicate 2/3/4)` are the next DRD items
  (`<6>`, `<10>`–`<12>`).
- [ ] Table 4-1 p. 32: 13 rows × 2 value columns, owner `4.4.2` — values match the PDF
  ✗ The 13 rows match p. 32, but the table continues on p. 33 (sections 6–9 and on) and that page is lost (H15).
  Exponents print flat (`1,3 10-3 hPa`).
- [x] Table 4-2 p. 35: 23 rows × 2 value columns, owner `4.4.3` — values match the PDF
  (section 1 "Mass" sits in the column headers instead of a row; exponents flat)
- [ ] Table 5-1 p. 46: 15 rows × 15 value columns, owner `5.2` — values match the PDF
  ✗ p. 46 only; continuation pp. 47–48 (structural integrity, thermal, EMC rows and the notes) lost (H15).
- [ ] Table 5-2 p. 49: 8 rows × 6 value columns, owner `5.2` — values match the PDF
  ✗ Rows 1–7 match p. 49, but row 7 is split in two and the continuation p. 50 (rows 8 shock, 9 micro-vibration)
  is lost (H15).
- [ ] Table 5-3 p. 55: 15 rows × 15 value columns, owner `5.3` — values match the PDF
  ✗ p. 55 only; continuation pp. 56–57 lost (H15).
- [ ] Table 5-4 p. 58: 8 rows × 6 value columns, owner `5.3` — values match the PDF
  ✗ p. 58 only; continuation p. 59 lost (H15).
- [ ] Table 5-5 p. 62: 15 rows × 15 value columns, owner `5.4` — values match the PDF
  ✗ p. 62 only; continuation pp. 63–64 lost (H15).
- [ ] Table 5-6 p. 65: 7 rows × 6 value columns, owner `5.4` — values match the PDF
  ✗ p. 65 only; continuation p. 66 (shock row and on) lost (H15).
- [ ] Table 6-1 p. 87: 17 rows × 4 value columns, owner `6.2` — values match the PDF
  ✗ p. 87 only; continuation pp. 88–89 lost (H15).
- [ ] Table 6-2 p. 90: 6 rows × 6 value columns, owner `6.2` — values match the PDF
  ✗ p. 90 only; continuation p. 91 (sinusoidal vibration and on) lost (H15).
- [ ] Table 6-3 p. 94: 16 rows × 4 value columns, owner `6.3` — values match the PDF
  ✗ p. 94 only; continuation pp. 95–96 lost (H15).
- [ ] Table 6-4 p. 97: 8 rows × 6 value columns, owner `6.3` — values match the PDF
  ✗ p. 97 only; continuation p. 98 (shock and on) lost (H15).
- [ ] Table 6-5 p. 101: 14 rows × 4 value columns, owner `6.4` — values match the PDF
  ✗ p. 101 only; continuation pp. 102–103 lost (H15).
- [ ] Table 6-6 p. 104: 8 rows × 6 value columns, owner `6.4` — values match the PDF
  ✗ p. 104 only; continuation p. 105 (shock and on) lost (H15).

### ECSS-E-ST-32-02C Rev.1

Source: `Active ECSS Standards_PDF-files (10Oct2025)/ECSS-E-ST-32-02C_Rev.1(15November2008).pdf`. Records: 418 (386 requirement, 0 recommendation, 32 permission, 0 guidance, 0 deleted).

- [ ] Requirement count 386 matches the PDF (first `4.2.1a` p. 18, last `5.7.2e` p. 75)
  ✗ Every "shall" sentence is in a requirement record, but `4.5.1.4c` p. 45 and `5.3.1a` p. 67 have no
  shall / should / may (they are "can" statements) and count as requirements: 384 (H14).
- [x] Spot checks (ID exists, text complete, kind right): `4.2.1a` p. 18, `4.3.3.1d` p. 26, `4.4.2.1f` p. 35, `4.4.4.3b` p. 42, `4.5.3.2h` p. 50, `4.6.2.2m` p. 60, `5.3.3d` p. 69, `5.7.2e` p. 75
- [x] Table 4-1 p. 23: 2 rows × 4 value columns, owner `4.3.1` — values match the PDF
- [x] Table 4-2 p. 34: 2 rows × 4 value columns, owner `4.4.1` — values match the PDF
- [x] Table 4-3 p. 34: 2 rows × 4 value columns — values match the PDF
- [x] Table 4-4 p. 34: 2 rows × 4 value columns — values match the PDF
- [x] Table 4-5 p. 44: 5 rows × 3 value columns, owner `4.5.1.1` — values match the PDF
  (values right; the FOSY column is shaded in the PDF and parsed as an empty label column; the NOTES block is
  parsed as a fifth row, H17)
- [x] Table 4-6 p. 47: 2 rows × 4 value columns, owner `4.5.2.1` — values match the PDF
- [x] Table 4-7 p. 50: 2 rows × 4 value columns, owner `4.5.3.1` — values match the PDF
- [ ] Table 4-8 p. 53: 6 rows × 3 value columns, owner `4.6.1.1` — values match the PDF
  ✗ Values and row order right, but rows 1–4 all carry the four application names together as their label, so
  a row cannot be told from another (H17).
- [x] Table 4-9 p. 60: 2 rows × 4 value columns, owner `4.6.2.1` — values match the PDF
- [x] Table 4-10 p. 62: 2 rows × 4 value columns, owner `4.6.3.1` — values match the PDF

### ECSS-E-ST-32-03C

Source: `Active ECSS Standards_PDF-files (10Oct2025)/ECSS-E-ST-32-03C(31July2008).pdf`. Records: 43 (41 requirement, 2 recommendation, 0 permission, 0 guidance, 0 deleted).

- [ ] Requirement count 41 matches the PDF (first `4.2a` p. 12, last `6.2d` p. 20)
  ✗ Should be 42: `5.5g` (p. 18) is lost, and `5.5f` stops after list item 2 (items 3–4 lost), after an equation
  (H14). `5.4.3b` and `5.4.3d` lose their formulas (H10).
- [x] Spot checks (ID exists, text complete, kind right): `4.2a` p. 12, `4.4e` p. 14, `4.4j` p. 14, `5.3a` p. 15, `5.4.3b` p. 17, `5.5c` p. 17, `5.7a` p. 19, `6.2d` p. 20
  (`5.4.3b` ends at its formula, H10)

### ECSS-E-ST-32-11C

Source: `Active ECSS Standards_PDF-files (10Oct2025)/ECSS-E-ST-32-11C(31July2008).pdf`. Records: 128 (119 requirement, 9 recommendation, 0 permission, 0 guidance, 0 deleted).

- [x] Requirement count 119 matches the PDF (first `4.1.2a` p. 26, last `6.4.2b` p. 56)
  (every "shall" sentence in a requirement record, every requirement record has a "shall")
- [x] Spot checks (ID exists, text complete, kind right): `4.1.2a` p. 26, `4.2.3a` p. 29, `5.2.1a` p. 32, `5.3.3e` p. 38, `5.4.2d` p. 40, `5.7.1.4a` p. 44, `5.8.2.2b` p. 48, `6.4.2b` p. 56
- [x] Table 5-1 p. 36: 3 rows × 1 value columns, owner `5.3.2.1` — values match the PDF (text table, by text)
- [x] Table 5-2 p. 47: 3 rows × 1 value columns, owner `5.8.1.1` — values match the PDF (text table, by text)
- [x] Table 5-3 p. 49: 6 rows × 1 value columns, owner `5.8.2.2` — values match the PDF
  (criterion names and limits share one cell, in order: MAC > 0,9 / < 3 % etc.)
- [x] Table 5-4 p. 49: 3 rows × 1 value columns, owner `D` — values match the PDF
  (values right; owner `D` looks wrong, check before adding to tests)
- [x] Table 6-1 p. 53: 4 rows × 2 value columns, owner `6.2.2` — values match the PDF

### ECSS-E-ST-33-01C Rev.2

Source: `Active ECSS Standards_PDF-files (10Oct2025)/ECSS-E-ST-33-01C-Rev.2(1March2019).pdf`. Records: 451 (406 requirement, 24 recommendation, 2 permission, 0 guidance, 19 deleted).

- [x] Requirement count 406 matches the PDF (first `4.2.2a` p. 16, last `G.2.1<5>c` p. 74)
  (every "shall" sentence in a requirement record, every requirement record has a "shall"; no machine IDs in
  this issue)
- [x] Spot checks (ID exists, text complete, kind right): `4.2.2a` p. 16, `4.7.3.1i` p. 24, `4.7.5.3.2c` p. 32, `4.7.5.4.12f` p. 38, `4.8.2.6.2b` p. 44, `4.8.3.3.9c` p. 50, `A.2.1<7>b` p. 60, `G.2.1<5>c` p. 74
- [x] Table 4-1 p. 25: 2 rows × 3 value columns, owner `4.7.3.3.2` — values match the PDF
- [x] Table 4-2 p. 30: 7 rows × 2 value columns, owner `4.7.5.3.1` — values match the PDF
- [x] Table 4-3 p. 33: 7 rows × 2 value columns, owner `4.7.5.3.3` — values match the PDF
- [x] Table 4-4 p. 52: 7 rows × 2 value columns, owner `4.8.3.3.14` — values match the PDF
- [x] Table 4-5 p. 52: 9 rows × 1 value columns, owner `4.8.3.3.14` — values match the PDF
- [ ] Table 4-6 p. 53: 7 rows × 1 value columns, owner `4.8.3.3.14` — values match the PDF
  ✗ The PDF has two calculation columns (ground, in-orbit); the parse puts both in one column, so rows 0 and 5
  hold two numbers each (H17). Informative example.
- [ ] Table 4-7 p. 53: 7 rows × 1 value columns, owner `G` — values match the PDF
  ✗ Same as Table 4-6, and the owner should be `4.8.3.3.14`, not `G`.

### NASA-SPEC-5022 w/Change 2

Source: `nasa/NASA-SPEC-5022 - 2026-01-15-NASA-SPEC-5022 w-Change 2 Final - Revalidated.pdf`. Records: 111 (81 requirement, 0 recommendation, 0 permission, 30 guidance, 0 deleted).

- [ ] Requirement count 81 matches the PDF (first `NCPR 1` p. 12, last `NCPR 79` p. 23)
  ✗ Should be 79: NCPR 1–79 all parsed (same set as the PDF), plus 2 false records from footnotes,
  `NCPR 9 / 4.2.1` p. 13 and `NCPR 35 / 4.4.2` p. 18 (H12).
- [x] Spot checks (ID exists, text complete, kind right): `NCPR 1` p. 12, `NCPR 11` p. 14, `NCPR 23` p. 15, `NCPR 34` p. 17, `NCPR 45` p. 20, `NCPR 56` p. 21, `NCPR 68` p. 22, `NCPR 79` p. 23

### NASA-STD-5002B

Source: `nasa/NASA-STD-5002 - Final Approved NASA-STD-5002_REV B - 03-10-2026.pdf`. Records: 149 (69 requirement, 0 recommendation, 0 permission, 80 guidance, 0 deleted).

- [ ] Requirement count 69 matches the PDF (first `LAR 1` p. 13, last `LAR 69 / 4.9.3.1` p. 27)
  ✗ Should be 67 requirements + 1 deleted. LAR 1–69 are in the body except LAR 68, which the PDF prints only in
  the Appendix A matrix (p. 34) and the change log, not in the body (source, parser right). LAR 7 (p. 14, a deleted
  requirement) is parsed as the requirement `LAR 7 / 4.1.6` (H12). `LAR 69 / 4.9.3.1` is the fifth check of LAR
  69's list, printed without a letter (p. 27): it belongs in LAR 69, not in its own record.
- [ ] Spot checks (ID exists, text complete, kind right): `LAR 1` p. 13, `LAR 11` p. 15, `LAR 20` p. 17, `LAR 30` p. 19, `LAR 40` p. 21, `LAR 50` p. 23, `LAR 59` p. 25, `LAR 69 / 4.9.3.1` p. 27
  ✗ 7/8 right; `LAR 69 / 4.9.3.1` as above.

### NASA-STD-5005D w/Change 2

Source: `nasa/NASA-STD-5005 - 2024-09-30-NASA-STD-5005D_Revalidation-Change-2.pdf`. Records: 430 (251 requirement, 0 recommendation, 0 permission, 179 guidance, 0 deleted).

- [x] Requirement count 251 matches the PDF (first `4.1a` p. 25, last `6.4.16c` p. 69)
  (every "shall" sentence in a requirement record, every requirement record has a "shall"; but see the IDs below.
  Subscripts are lost in the text, e.g. `LO /GO` on p. 55, and `6.4.16c` reads `b e`.)
- [x] Spot checks (ID exists, text complete, kind right): `4.1a` p. 25, `4.6.2.1b` p. 31, `5.2.8b` p. 37, `5.4.9.1 req 1` p. 44, `6 req 1` p. 51, `6.3.1.4.2 req 2` p. 59, `6.4.4c` p. 64, `6.4.16c` p. 69
- [ ] Parser flag "tag defined twice in the body" on 20 records, e.g. `6.3.1.3a (duplicate)` p. 55, `6.3.1.4.2a (duplicate)` p. 57, `6.3.1.4.2b (duplicate)` p. 59, `6.4.13c (duplicate)` p. 68
  ✗ Not duplicates in the source: headings are missed (H13), so their items take the previous section's number.
  Most level-5 headings under 6.3.1.3, 6.3.1.4 and 6.3.1.5 (pp. 54–61) and the level-3 heading 6.4.14 (p. 68)
  are missed: `6.3.1.3a (duplicate)` is printed 6.3.1.3.2a,
  `6.4.13a–c (duplicate)` are printed 6.4.14a–c. About 37 records carry a wrong ID (pp. 54–61 and 68), not only
  the 20 flagged.

### NASA-STD-5006A w/Change 2

Source: `nasa/NASA-STD-5006 - 2021-11-18-NASA-STD-5006A-w-Chg-2-Reval-Final.pdf`. Records: 175 (137 requirement, 0 recommendation, 0 permission, 38 guidance, 0 deleted).

- [ ] Requirement count 137 matches the PDF (first `GWR 5` p. 12, last `GWR 142` p. 31)
  ✗ Should be 138: GWR 103 (top of p. 26) is in no record and not in the unparsed list (H14). GWR 1–4 are not in
  this issue (source).
- [x] Spot checks (ID exists, text complete, kind right): `GWR 5` p. 12, `GWR 24` p. 14, `GWR 44` p. 16, `GWR 63` p. 19, `GWR 83` p. 21, `GWR 102` p. 24, `GWR 123` p. 28, `GWR 142` p. 31

### NASA-STD-5008B w/Change 2

Source: `nasa/NASA-STD-5008 - 2024-09-30-NASA-STD-5008B-w-Change-2-Final-Revalidation.pdf`. Records: 363 (314 requirement, 0 recommendation, 0 permission, 49 guidance, 0 deleted).

- [ ] Requirement count 314 matches the PDF (first `PCR 15` p. 18, last `PCR 333` p. 55)
  ✗ The body prints 319 tags (PCR 15–333); 313 are records. PCR 179–181 (p. 38) and PCR 230–231 (p. 43) are
  `A.`/`B.`/`C.` items with their own tags, merged into `PCR 178` and `PCR 229`; PCR 249 (p. 45) sits inside the
  guidance record `4.5.2.2 guidance 3` (H14). `PCR 277 / 4.5.8` (p. 48) is a false record holding a footnote
  marker (H12). Should be 319.
- [x] Spot checks (ID exists, text complete, kind right): `PCR 15` p. 18, `PCR 60` p. 27, `PCR 104` p. 31, `PCR 149` p. 35, `PCR 197` p. 40, `PCR 244` p. 44, `PCR 288` p. 50, `PCR 333` p. 55
- [ ] Table 1 p. 48: 16 rows × 2 value columns, owner `PCR 277` — values match the PDF
  ✗ Values present, but the first group heading is in the column names, the other group headings are rows with
  the heading in both cells, so a zone row does not say which existing coating it is for; the footnotes are a data
  row (H17).

### NASA-STD-5009C

Source: `nasa/NASA-STD-5009 - 2023-08-03-NASA-STD-5009C-Approved.pdf`. Records: 123 (75 requirement, 0 recommendation, 0 permission, 48 guidance, 0 deleted).

- [ ] Requirement count 75 matches the PDF (first `NER 1` p. 16, last `NER 74 / 4.5.5` p. 33)
  ✗ Should be 74: NER 1–74 all parsed (same set as the PDF); `NER 74 / 4.5.5` p. 33 is a false record made of
  the table captions and notes (H12).
- [ ] Spot checks (ID exists, text complete, kind right): `NER 1` p. 16, `NER 12` p. 19, `NER 22` p. 20, `NER 33` p. 24, `NER 43` p. 25, `NER 54` p. 28, `NER 64` p. 30, `NER 74 / 4.5.5` p. 33
  ✗ 7/8 right; `NER 74 / 4.5.5` as above.
- [ ] Table 1 p. 33: 14 rows × 4 value columns, owner `NER 1` — values match the PDF
  ✗ Values present, but sub-rows are stacked in one cell (e.g. the eddy-current open-surface row holds three
  thickness ranges and three a / c pairs), `≤` signs are lost, the NDE-method headings are data rows with the
  heading in every cell, and the column names carry "/ Eddy Current NDE" (H17).
- [ ] Table 2 p. 34: 14 rows × 4 value columns, owner `NER 1` — values match the PDF
  ✗ Same as Table 1 (inch version).
- [ ] Table 1 p. 37: 11 rows × 4 value columns, owner `NER 1` — values match the PDF
  ✗ Not a second table: the copy of Table 1 inside the Appendix A requirements matrix (pp. 37–38), with the same
  table ID as the body table (H17). Should be dropped.
- [ ] Table 2 p. 39: 12 rows × 4 value columns, owner `NER 1` — values match the PDF
  ✗ Same: the Appendix A copy of Table 2.

### NASA-STD-5012C

Source: `nasa/NASA-STD-5012 - Final NASA-STD-5012C 12-31-2025.pdf`. Records: 57 (30 requirement, 0 recommendation, 0 permission, 27 guidance, 0 deleted).

- [ ] Requirement count 30 matches the PDF (first `PSER 1` p. 17, last `PSER 28` p. 31)
  ✗ Should be 28: PSER 1–28 all parsed (same set as the PDF), plus 2 false records, `PSER 3 / 5` p. 19 (the
  Table 1 notes) and `PSER 27 / 9.5.1` p. 31 (an equation) (H12).
- [x] Spot checks (ID exists, text complete, kind right): `PSER 1` p. 17, `PSER 4` p. 20, `PSER 8` p. 21, `PSER 12` p. 23, `PSER 17` p. 25, `PSER 21` p. 28, `PSER 25` p. 29, `PSER 28` p. 31
- [ ] Table 1 p. 19: 20 rows × 4 value columns, owner `PSER 3` — values match the PDF
  ✗ **Numbers wrong.** Footnote superscripts are fused into the values and parsed as digits: the yield analysis
  FOS 1.10 with note 5 reads `1.105` (value 1.105), 2.0 with note 8 reads `2.08`, 1.50 with notes 6,7 reads
  `1.506,7`, 1.20 with note 6 reads `1.206`, 1.70 with note 10 reads `1.7010`, 1.50 with note 5 reads `1.505`
  (H17). Notes 1–9 are not in `footnotes`; group headings are empty rows. Fix before any answer uses this table.
- [ ] Table 2 p. 32: 2 rows × 5 value columns — values match the PDF
  ✗ Not a data table: the first page of the Appendix A requirements matrix (continues on p. 33). Should be dropped.

### NASA-STD-5017B

Source: `nasa/NASA-STD-5017 - 2022-12-06-NASA-STD-5017B-Approved.pdf`. Records: 192 (92 requirement, 0 recommendation, 0 permission, 100 guidance, 0 deleted).

- [ ] Requirement count 92 matches the PDF (first `DDMR 1` p. 17, last `DDMR 90` p. 55)
  ✗ Should be 90: DDMR 1–90 all parsed (same set as the PDF), plus 2 false records, `DDMR 39 / 4.9.7` p. 34 (the
  NOTE under Table 3) and `DDMR 60 / 4.15.1` p. 45 (figure labels) (H12).
- [ ] Spot checks (ID exists, text complete, kind right): `DDMR 1` p. 17, `DDMR 14` p. 24, `DDMR 27` p. 30, `DDMR 39 / 4.9.7` p. 34, `DDMR 52` p. 41, `DDMR 64` p. 46, `DDMR 77` p. 51, `DDMR 90` p. 55
  ✗ 7/8 right; `DDMR 39 / 4.9.7` as above.
- [x] Table 3 p. 34: 4 rows × 4 value columns, owner `DDMR 38` — values match the PDF
  (the NOTE under the table is a false record, not a footnote)
- [x] Table 4 p. 87: 2 rows × 2 value columns — values match the PDF
- [ ] Table 5 p. 96: 2 rows × 12 value columns — values match the PDF
  ✗ R / AN values right, but the rotated column headers are reversed and letter-spaced, the first column name is
  the label column, and the legend is a data row (H17).
- [x] Table 6 p. 96: 14 rows × 2 value columns — values match the PDF (footnote (1) not captured)
- [ ] Table 7 p. 100: 1 rows × 8 value columns — values match the PDF
  ✗ Same rotated-header problem as Table 5.
- [ ] ✗ Not parsed: Table 1 p. 21 (minimum safety factors for the torque margin equation) and
  Table 2 p. 25 (stepper motor margin methods) (H16). Table 1 is the main numeric table of the standard.

### NASA-STD-5018 w/Change 1

Source: `nasa/NASA-STD-5018 - NASA-STD-2018_Revalidated - 01-30-2026.pdf`. Records: 294 (234 requirement, 0 recommendation, 0 permission, 60 guidance, 0 deleted).

- [x] Requirement count 234 matches the PDF (first `4.2a` p. 16, last `5.12 req 1` p. 45)
  (every "shall" sentence in a requirement record, every requirement record has a "shall")
- [x] Spot checks (ID exists, text complete, kind right): `4.2a` p. 16, `4.5.4 req 1` p. 22, `4.7.12b` p. 27, `4.10.1 req 1` p. 31, `5.3.6a` p. 35, `5.7.4f` p. 39, `5.8.6b` p. 42, `5.12 req 1` p. 45
- [ ] Parser flag "tag defined twice in the body" on 2 records, e.g. `4.7.2a (duplicate)` p. 23, `4.7.2b (duplicate)` p. 24
  ✗ Not duplicates: heading 4.7.3 (p. 23, its title has a ® sign) is missed, so 4.7.3a–b get 4.7.2 IDs (H13).
- [x] Table 1 p. 22: 4 rows × 2 value columns — values match the PDF (the `*` note is not captured)

### NASA-STD-5020B

Source: `nasa/NASA-STD-5020B Revalidated 1-5-2026.pdf`. Records: 210 (38 requirement, 0 recommendation, 0 permission, 172 guidance, 0 deleted).

- [ ] Requirement count 38 matches the PDF (first `TFSR 1` p. 17, last `TFSR 32` p. 45)
  ✗ Should be 32: TFSR 1–32 all parsed (same set as the PDF), plus 6 false records, `TFSR 5 / 4.3.1` p. 21,
  `TFSR 8 / 4.4.1` p. 28, `TFSR 9 / 4.4.2` p. 30, `TFSR 11 / 4.4.4` p. 33 (equations), `TFSR 23 / 4.7.4` p. 41
  (figure labels) and `TFSR 29 / 4.8.4` p. 44 (a paragraph without "shall") (H12).
- [ ] Spot checks (ID exists, text complete, kind right): `TFSR 1` p. 17, `TFSR 5 / 4.3.1` p. 21, `TFSR 9 / 4.4.2` p. 30, `TFSR 13` p. 34, `TFSR 18` p. 38, `TFSR 23` p. 41, `TFSR 28` p. 44, `TFSR 32` p. 45
  ✗ 6/8 right; `TFSR 5 / 4.3.1` and `TFSR 9 / 4.4.2` are equation fragments, not requirements.
- [x] Table 1 p. 22: 4 rows × 3 value columns — values match the PDF
  (values right; the two footnotes are a fourth data row, H17)
- [x] Table 2 p. 24: 5 rows × 3 value columns — values match the PDF (the R / NR legend is a fifth data row)
- [x] Table 3 p. 25: 4 rows × 2 value columns, owner `TFSR 7` — values match the PDF
  (the three footnotes are a fourth data row; nothing continues on p. 26)
- [x] Table 4 p. 39: 4 rows × 1 value columns, owner `TFSR 19` — values match the PDF (footnote as a fourth row)
- [ ] Table 5 p. 49: 10 rows × 8 value columns — values match the PDF
  ✗ The PDF has four m / s column pairs (m = 2 … 100); only the last pair (m = 40 … 100) is kept, as 2 of the 8
  columns; m = 2 … 35 are lost (H17).
- [x] Table 6 p. 49: 3 rows × 10 value columns — values match the PDF
- [ ] Table 7 p. 98: 2 rows × 5 value columns — values match the PDF
  ✗ Each column's 11 values are joined into one cell, and the assumptions box is the second row (H17).
- [ ] Table 8 p. 100: 12 rows × 1 value columns — values match the PDF
  ✗ Garbled: the case columns are joined into one cell per row (H17).

### NASA-STD-5023

Source: `nasa/NASA-STD-5023 Final Version 8-19-2026_0.pdf`. Records: 295 (105 requirement, 0 recommendation, 0 permission, 190 guidance, 0 deleted).

- [x] Requirement count 105 matches the PDF (first `VDVR 1` p. 16, last `VDVR 105` p. 69)
  (VDVR 1–105 all parsed, same set as the PDF, no false records)
- [x] Spot checks (ID exists, text complete, kind right): `VDVR 1` p. 16, `VDVR 16` p. 26, `VDVR 31` p. 35, `VDVR 46` p. 40, `VDVR 60` p. 49, `VDVR 75` p. 56, `VDVR 90` p. 61, `VDVR 105` p. 69
- [x] Table 2 p. 24: 1 rows × 1 value columns, owner `VDVR 12` — values match the PDF (one text cell)
- [ ] ✗ Not parsed: Table 1 (minimum safety factors for torque and force margins; caption at the foot of p. 18,
  body on p. 19) and Table 3 (allowable bearing contact stress; caption at the foot of p. 43, body on p. 44) (H16).

### NASA-STD-7001C

Source: `nasa/NASA-STD-7001C  - Final 7-14-2026.pdf`. Records: 146 (68 requirement, 0 recommendation, 0 permission, 78 guidance, 0 deleted).

- [ ] Requirement count 68 matches the PDF (first `PVTR 1` p. 16, last `PVTR 64` p. 30)
  ✗ Should be 64: PVTR 1–64 all parsed (same set as the PDF), plus 4 false records, `PVTR 8 / 4.3.3.1` p. 18
  (the last line of Table 2 and the tail of a sentence), `PVTR 12 / 4.3.3.5` p. 19 (the two methods of PVTR 12's list,
  which belong in PVTR 12), `PVTR 60 / 4.5.2` p. 29 (an equation) and `PVTR 62 / 4.5.4` p. 30 (the tail of a sentence)
  (H12).
- [x] Spot checks (ID exists, text complete, kind right): `PVTR 1` p. 16, `PVTR 10` p. 19, `PVTR 18` p. 21, `PVTR 28` p. 23, `PVTR 37` p. 25, `PVTR 47` p. 26, `PVTR 56` p. 28, `PVTR 64` p. 30
- [x] Table 1 p. 16: 12 rows × 1 value columns — values match the PDF
- [ ] ✗ Not parsed: Table 2 p. 18 (component minimum workmanship random vibration spectrum, 5 breakpoints and the
  overall level; boxed, no grid) (H16).

### NASA-STD-7002B w/Change 1

Source: `nasa/NASA-STD-7002B-w-Change-1.pdf`. Records: 103 (64 requirement, 0 recommendation, 0 permission, 39 guidance, 0 deleted).

- [ ] Requirement count 64 matches the PDF (first `PTR 1` p. 14, last `PTR 63` p. 25)
  ✗ Should be 63: PTR 1–63 all parsed (same set as the PDF), plus the false record `PTR 1 / 4.1` p. 15 (the
  Table 1 legend) (H12).
- [x] Spot checks (ID exists, text complete, kind right): `PTR 1` p. 14, `PTR 9` p. 17, `PTR 18` p. 19, `PTR 27` p. 21, `PTR 36` p. 22, `PTR 45` p. 23, `PTR 54` p. 24, `PTR 63` p. 25
- [ ] Table 1 p. 15: 30 rows × 3 value columns, owner `PTR 1` — values match the PDF
  ✗ The printed marks (1, 2, 2,3, >, 6, 7) are right, but the grey shading that marks a required test is lost, so
  the parsed table does not say which tests are required; the legend and the (4) / (5) markers are lost (H17).
- [x] Table 2 p. 16: 2 rows × 2 value columns, owner `PTR 3` — values match the PDF

### NASA-STD-7003A

Source: `nasa/NASA-STD-7003A.pdf`. Records: 67 (24 requirement, 0 recommendation, 0 permission, 43 guidance, 0 deleted).

- [x] Requirement count 24 matches the PDF (first `4.1 req 1` p. 20, last `4.8 req 4` p. 27)
  (every "shall" sentence in a requirement record; IDs are the tagless `4.x req n` form, H9)
- [x] Spot checks (ID exists, text complete, kind right): `4.1 req 1` p. 20, `4.2 req 1` p. 20, `4.3 req 3` p. 21, `4.3 req 6` p. 21, `4.4 req 2` p. 22, `4.4 req 5` p. 22, `4.8 req 1` p. 27, `4.8 req 4` p. 27
- [x] Table 1 p. 10: 2 rows × 3 value columns — values match the PDF
- [x] Table 2 p. 38: 1 rows × 11 value columns — values match the PDF
