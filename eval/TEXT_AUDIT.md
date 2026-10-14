# Text audit of the release tree (C4)

`python scripts/audit_standards_text.py --docs documents` on 9 October 2026: 83 tracked text files against all
285 catalogued documents (superseded ones included), 0 parse failures. First run 20.5 min (cold parse cache),
re-run 1.4 s. Locations, lengths and IDs only, never the matched text.

## First run: 9 runs of >= 12 words, 1 table row

| Location | Match | Source | Decision |
| --- | --- | --- | --- |
| `eval/questions.yaml:158`, `eval/REVIEW.md:99` (fs-009) | 14 words | ECSS-E-ST-32-01C Rev.2 | sentence, paraphrased |
| `eval/questions.yaml:187`, `eval/REVIEW.md:119` (fs-011) | 26 words | ECSS-E-ST-32-01C Rev.2 | sentence, paraphrased |
| `eval/questions.yaml:266`, `eval/REVIEW.md:169` (fs-016) | 13 words | ECSS-E-ST-32-01C Rev.2 | sentence, paraphrased |
| `README.md:106`, `documents/README.md:12` | 13 words | 6 NASA documents' reference lists | the title of NASA-STD-5001: bibliographic, kept |
| `tests/test_real_documents.py:221` | 17 words | ECSS-Q-ST-70C Rev.2 | one row of compatibility codes (digits only): kept |
| `tests/test_real_documents.py:255` | 3 fields, row copied whole | NASA-STD-5001B w/Change 3, Table 7 | three factors (numbers only): kept |

The paraphrases keep every number, unit and requirement ID; retrieval is unchanged (questions and expected IDs
untouched, see `eval/RESULTS.md`).

## Re-run after the paraphrases: 3 runs, 1 table row, all accepted above

The accepted hits are in `scripts/audit_allowlist.yaml` (file, kind, length, source ID; no line numbers).
The script lists them as "accepted" and exits 0 on them. D1 re-runs it: any hit not in the allowlist needs a decision.

## Re-run 10 October 2026 (round 1: new README, A5 handbook sections)

94 text files against 287 parsed documents, 0 parse failures, 20.7 min (cold cache: A5 changed the parser).
The `README.md` title hit is gone (C8 rewrote the README). Two hits in `documents/README.md`, both titles in its
documents table that handbook reference lists now repeat, because A5 turned handbook prose into records:

| Location | Match | Source | Decision |
| --- | --- | --- | --- |
| `documents/README.md:10` | 12 words | ECSS-E-HB-32-26A | the title of ECSS-E-ST-32-10: bibliographic, kept |
| `documents/README.md:12` | 13 words | 7 NASA documents, ECSS-E-HB-32-23A | the title of NASA-STD-5001 (accepted above): kept |

The allowlist's `source` may now be a list of prefixes. With it: 0 new hits, 4 accepted, exit 0.

## Re-run 10 October 2026 (round 3: parser fixes H8–H17, B3 tests)

97 text files against 287 parsed documents, 0 parse failures, 21.2 min (cold cache: the parser changed). One new
hit, accepted:

| Location | Match | Source | Decision |
| --- | --- | --- | --- |
| `tests/test_real_documents.py` (5005D test) | 2 fields, row copied whole | ECSS-E-HB-31-01 Part 5A, Table 5-86 | a list of NASA-STD-5005D requirement IDs; two short IDs coincide with a handbook table row: kept |

With it: 0 new hits, 5 accepted, exit 0.

## Re-run 12 October 2026 (round 4: table fixes H16/H17, NASA line fixes, 8 more verified)

105 tracked text files against 287 parsed documents (cold parse cache after the parser changes). 18 new hits, none
copied text: 1 × 12 words in `documents/README.md` (NASA-STD-5001's title, now also found in NASA-HDBK-7005's reference
list) and 17 short table rows that coincide with rows of ECSS-E-HB-31-01 thermal handbook tables, which round 4 splits
into shorter rows: health-report count rows (`eval/CORPUS_HEALTH*.md`, `tests/test_health.py`; Part 14A Table 8-8)
and invented test fixtures (list markers, one-letter column names, two invented numbers; Part 11A Table 5-2, Part 5A
Table 5-86). All accepted in `scripts/audit_allowlist.yaml` (12 entries); re-run: 0 new hits, 23 accepted, exit 0.

## Re-run 12 October 2026 (round 5: H18/H19 table fixes, 3 more verified; D1)

107 tracked text files against 287 parsed documents (cold parse cache after the parser changes; 20 min). Three new
hits, all table rows. Results:

| Location | Match | Source | Decision |
| --- | --- | --- | --- |
| `tests/test_table_10_03.py` (two group-row fixtures) | 4 fields, row copied whole | ECSS-E-ST-10-03C Tables 6-1 / 6-3 / 6-5 | a real test name, clause number and mark had been copied into a worker's fixture: **replaced with invented values** |
| `tests/test_real_documents.py` (7002B test) | 6 fields, row copied whole | ECSS-E-HB-32-23A Table 7-2 | a list of footnote markers ("1" to "6", ">", "shaded") coinciding with a row of single digits: accepted |

Two short real phrases in the new fixtures were below the audit's thresholds: a legend text (shading test) and a
test name (10-03C row test). They were replaced with invented text as well. Re-run: 0 new hits, 24 accepted, exit 0.
